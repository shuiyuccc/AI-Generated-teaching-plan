"""
API服务器 - 提供前端调用的接口
"""
import os
import sys
import io
import json
import queue
import threading
import time
import uuid
import logging
from datetime import datetime
from urllib.parse import quote
from flask import Flask, request, jsonify, send_from_directory, Response, stream_with_context
from flask_cors import CORS

RENDER_DATA_DIR = os.environ.get('RENDER_DATA_DIR', '')

def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath('.'), relative_path)
def get_base_dir():
    if hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_base_dir()
sys.path.insert(0, BASE_DIR)

from main import batch_generate_lesson_plans, generate_lesson_plan_doc
from config import DEFAULT_FIXED_COURSE_INFO, save_settings_to_file, load_settings_from_file, reload_config, SETTINGS_FILE, get_current_model_config




from document_processor import extract_document_content, get_document_summary
from excel_utils import create_lesson_plan_template, parse_lesson_plan_excel

DATA_DIR = RENDER_DATA_DIR if RENDER_DATA_DIR else BASE_DIR

UPLOAD_DIR = os.path.join(DATA_DIR, 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

SESSION_DIR = os.path.join(DATA_DIR, 'sessions')
os.makedirs(SESSION_DIR, exist_ok=True)

uploaded_documents = {}

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {"origins": "*", "supports_credentials": True},
    r"/download/*": {"origins": "*", "supports_credentials": True},
    r"/*": {"origins": "*"}
})
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

STATIC_DIR = os.path.join(BASE_DIR, 'frontend', 'dist')
OUTPUT_DIR = os.path.join(DATA_DIR, 'output')

# Log startup info
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info(f"Flask app initialized")
logger.info(f"BASE_DIR: {BASE_DIR}")
logger.info(f"DATA_DIR: {DATA_DIR}")
logger.info(f"UPLOAD_DIR: {UPLOAD_DIR}")
logger.info(f"OUTPUT_DIR: {OUTPUT_DIR}")

os.makedirs(OUTPUT_DIR, exist_ok=True)



generation_sessions = {}
sessions_lock = threading.Lock()


def save_session_to_file(session_id, session_data):
    try:
        session_file = os.path.join(SESSION_DIR, f'{session_id}.json')
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"保存会话文件失败: {e}")


def load_session_from_file(session_id):
    try:
        session_file = os.path.join(SESSION_DIR, f'{session_id}.json')
        if os.path.exists(session_file):
            with open(session_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logging.error(f"加载会话文件失败: {e}")
    return None





def update_session(session_id, data):
    with sessions_lock:
        if session_id not in generation_sessions:
            generation_sessions[session_id] = {
                'created_at': datetime.now().isoformat(),
                'status': 'pending',
                'progress': 0,
                'results': []
            }
        generation_sessions[session_id].update(data)
        generation_sessions[session_id]['updated_at'] = datetime.now().isoformat()
        # 保存到文件
        save_session_to_file(session_id, generation_sessions[session_id])


def get_session(session_id):
    with sessions_lock:
        session = generation_sessions.get(session_id)
        if session:
            return session
        # 尝试从文件加载
        session = load_session_from_file(session_id)
        if session:
            generation_sessions[session_id] = session
        return session





@app.route('/api/session', methods=['POST'])
def create_session():
    session_id = str(uuid.uuid4())
    update_session(session_id, {'status': 'ready'})
    return jsonify({'success': True, 'session_id': session_id})


@app.route('/api/session/<session_id>', methods=['GET'])
def get_session_status(session_id):
    logging.debug(f"获取会话状态: {session_id}")
    session = get_session(session_id)
    logging.debug(f"会话数据: {session}")
    if not session:
        logging.debug(f"会话不存在")
        return jsonify({'success': False, 'message': '会话不存在'}), 404
    
    logging.debug(f"返回会话状态: {session.get('status')}")
    return jsonify({
        'success': True,
        'session': session
    })


@app.route('/api/logs/<session_id>/poll')
def poll_logs(session_id):
    session = get_session(session_id)
    
    if not session:
        return jsonify({'success': False, 'message': '会话不存在'}), 404
    
    return jsonify({
        'success': True,
        'status': session.get('status'),
        'progress': session.get('progress', 0),
        'results': session.get('results', []),
        'current_topic': session.get('current_topic', '')
    })





@app.route('/api/generate', methods=['POST'])
def generate():
    session_id = request.headers.get('X-Session-ID', request.json.get('session_id', 'default'))

    update_session(session_id, {
        'status': 'generating',
        'progress': 0,
        'results': []
    })

    try:
        data = request.json
        if not data:
            update_session(session_id, {'status': 'error', 'error': '请提供生成参数'})
            return jsonify({'success': False, 'message': '请提供生成参数'}), 400

        # 检查 API Key 是否已配置
        from config import get_current_model_config
        current_cfg = get_current_model_config()
        if not current_cfg.get('api_key'):
            update_session(session_id, {'status': 'error', 'error': 'api_key_missing'})
            return jsonify({
                'success': False,
                'error_type': 'api_key_missing',
                'message': f'请先配置 {current_cfg.get("name", "LLM")} API Key',
                'setup_url': '/setup'
            }), 401

        fixed_course_info = data.get('fixed_course_info', {})
        variable_course_info = data.get('variable_course_info', {})
        lesson_index = data.get('lesson_index', 1)

        if not variable_course_info:
            update_session(session_id, {'status': 'error', 'error': '请提供课时信息'})
            return jsonify({'success': False, 'message': '请提供课时信息'}), 400

        complete_fixed_info = {**DEFAULT_FIXED_COURSE_INFO, **fixed_course_info}
        course_info = {**complete_fixed_info, **variable_course_info}
        
        lesson_id = str(lesson_index)
        docs = uploaded_documents.get(lesson_id, [])
        if docs:
            course_info['参考文档'] = [
                {'filename': doc.get('filename', '未命名文档'), 'content': doc.get('content', '')}
                for doc in docs
            ]
            logging.info(f"已关联 {len(docs)} 个参考文档")

        topic = course_info.get('课题名称', f'课时{lesson_index}')
        safe_topic = topic.replace('\\', '-').replace('/', '-').replace(':', '-').replace('*', '-').replace('?', '-').replace('"', '-').replace('<', '-').replace('>', '-').replace('|', '-')
        file_name = f"{lesson_index:02d}_{safe_topic}.docx"
        output_path = os.path.join(OUTPUT_DIR, file_name)

        update_session(session_id, {'progress': 20, 'current_topic': topic})

        template_path = os.path.join(BASE_DIR, 'moban.docx')
        success = generate_lesson_plan_doc(
            template_path=template_path,
            output_path=output_path,
            course_info=course_info,
            use_mock=False
        )

        if success == "invalid_api_key":
            update_session(session_id, {'status': 'error', 'error_type': 'invalid_api_key'})
            return jsonify({
                'success': False,
                'error_type': 'invalid_api_key',
                'message': 'DeepSeek API Key无效或已过期'
            }), 401

        update_session(session_id, {'progress': 100})

        if success and os.path.exists(output_path):
            result = {
                'topic': topic,
                'status': '成功',
                'file_name': file_name,
                'file_url': f'/download/{file_name}'
            }
            update_session(session_id, {'status': 'completed', 'results': [result]})
            return jsonify({'success': True, 'result': result})
        else:
            update_session(session_id, {'status': 'error', 'error': '文件未生成'})
            return jsonify({'success': False, 'message': '文件未生成'})

    except Exception as e:
        update_session(session_id, {'status': 'error', 'error': str(e)})
        return jsonify({'success': False, 'message': f'生成失败: {str(e)}'}), 500


@app.route('/api/batch-generate', methods=['POST'])
def batch_generate():
    session_id = request.headers.get('X-Session-ID', request.json.get('session_id', 'default'))

    update_session(session_id, {
        'status': 'generating',
        'progress': 0,
        'results': [],
        'total_lessons': 0,
        'current_lesson': 0
    })

    # 配置 jiaoan logger
    jiaoan_logger = logging.getLogger('jiaoan')
    jiaoan_logger.setLevel(logging.DEBUG)

    try:
        data = request.json
        if not data:
            update_session(session_id, {'status': 'error', 'error': '请提供生成参数'})
            return jsonify({'success': False, 'message': '请提供生成参数'}), 400

        # 检查 API Key 是否已配置
        from config import get_current_model_config
        current_cfg = get_current_model_config()
        if not current_cfg.get('api_key'):
            update_session(session_id, {'status': 'error', 'error': 'api_key_missing'})
            return jsonify({
                'success': False,
                'error_type': 'api_key_missing',
                'message': f'请先配置 {current_cfg.get("name", "LLM")} API Key',
                'setup_url': '/setup'
            }), 401

        fixed_course_info = data.get('fixed_course_info', {})
        variable_course_infos = data.get('variable_course_infos', [])

        if not variable_course_infos:
            update_session(session_id, {'status': 'error', 'error': '请至少提供一个课时信息'})
            return jsonify({'success': False, 'message': '请至少提供一个课时信息'}), 400

        logging.info("=" * 50)
        logging.info("🎯 开始批量生成教案")
        logging.info(f"📚 总课时数: {len(variable_course_infos)}")
        logging.info("=" * 50)

        complete_fixed_info = {**DEFAULT_FIXED_COURSE_INFO, **fixed_course_info}
        
        total_lessons = len(variable_course_infos)
        # 设置初始的 current_topic
        first_topic = variable_course_infos[0].get('课题名称', '课时1') if variable_course_infos else '准备中...'
        update_session(session_id, {
            'total_lessons': total_lessons,
            'current_topic': first_topic
        })
        
        results = []
        
        for i, lesson in enumerate(variable_course_infos, 1):
            lesson_id = str(lesson.get('id', ''))
            logging.info(f"📖 正在生成课时 {i}/{total_lessons}: {lesson.get('课题名称', '未命名')}")
            
            if lesson_id and lesson_id in uploaded_documents:
                docs = uploaded_documents[lesson_id]
                if docs:
                    lesson['参考文档'] = [
                        {'filename': doc['filename'], 'content': doc['content']}
                        for doc in docs
                    ]
                    logging.info(f"📎 已关联 {len(docs)} 个参考文档: {', '.join([d['filename'] for d in docs])}")
            
            progress = int((i / total_lessons) * 100)
            topic = lesson.get('课题名称', f'课时{i}')
            update_session(session_id, {
                'current_lesson': i,
                'current_topic': topic,
                'progress': progress
            })
            
            safe_topic = topic.replace('\\', '-').replace('/', '-').replace(':', '-').replace('*', '-').replace('?', '-').replace('"', '-').replace('<', '-').replace('>', '-').replace('|', '-')
            file_name = f"{i:02d}_{safe_topic}.docx"
            output_path = os.path.join(OUTPUT_DIR, file_name)
            
            course_info = {**complete_fixed_info, **lesson}
            
            logging.info("📝 正在调用 AI 生成教案内容...")
            
            template_path = os.path.join(BASE_DIR, 'moban.docx')
            success = generate_lesson_plan_doc(
                template_path=template_path,
                output_path=output_path,
                course_info=course_info,
                use_mock=False
            )
            
            if success and os.path.exists(output_path):
                results.append({
                    'topic': topic,
                    'status': '成功',
                    'file_name': file_name,
                    'file_url': f'/download/{file_name}'
                })
                logging.info(f"✅ 课时 {i} 生成成功: {topic}")
            else:
                results.append({
                    'topic': topic,
                    'status': '失败',
                    'message': '文件未生成'
                })
                logging.error(f"❌ 课时 {i} 生成失败: {topic}")
            
            update_session(session_id, {'results': results})
        
        update_session(session_id, {
            'status': 'completed',
            'progress': 100,
            'results': results
        })
        
        logging.info("=" * 50)
        logging.info(f"🎉 全部完成！成功 {len([r for r in results if r['status'] == '成功'])} 个，失败 {len([r for r in results if r['status'] == '失败'])} 个")
        logging.info("=" * 50)
        
        return jsonify({'success': True, 'results': results})

    except Exception as e:
        logging.error(f"生成失败: {str(e)}")
        update_session(session_id, {'status': 'error', 'error': str(e)})
        return jsonify({'success': False, 'message': f'生成失败: {str(e)}'}), 500


@app.route('/api/upload-document', methods=['POST'])
def upload_document():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '没有上传文件'}), 400
        
        file = request.files['file']
        lesson_id = request.form.get('lesson_id', '')
        
        if file.filename == '':
            return jsonify({'success': False, 'message': '文件名为空'}), 400
        
        allowed_extensions = {'.docx', '.doc', '.pptx', '.ppt', '.xlsx', '.xls', '.txt', '.pdf'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            return jsonify({'success': False, 'message': f'不支持的文件格式: {file_ext}'}), 400
        
        file_content = file.read()
        original_size = len(file_content)
        logging.info(f"接收到文件: {file.filename}, 原始大小: {original_size} 字节")
        
        safe_filename = f"{lesson_id}_{int(time.time())}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, safe_filename)
        
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        saved_size = os.path.getsize(file_path)
        logging.info(f"文件已保存到: {file_path}")
        logging.info(f"保存后大小: {saved_size} 字节")
        
        if saved_size != original_size:
            logging.warning(f"文件大小不匹配! 原始: {original_size}, 保存: {saved_size}")
            return jsonify({'success': False, 'message': '文件保存不完整'}), 500
        
        content = extract_document_content(file_path)
        
        if content is None:
            error_msg = f"❌ 文档解析失败: {file.filename} - 无法提取文档内容，请检查文件格式是否正确或文件是否损坏"
            logging.error(error_msg)
            # 删除上传的文件
            try:
                os.remove(file_path)
            except:
                pass
            return jsonify({
                'success': False,
                'message': error_msg,
                'error_type': 'parse_failed',
                'filename': file.filename
            }), 400
        
        content_summary = content[:500] if content else ""
        
        doc_info = {
            'filename': file.filename,
            'filepath': file_path,
            'content': content,
            'content_summary': content_summary,
            'file_size': saved_size,
            'upload_time': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 追加文档到列表，而不是覆盖
        if lesson_id not in uploaded_documents:
            uploaded_documents[lesson_id] = []
        uploaded_documents[lesson_id].append(doc_info)
        
        success_msg = f"✅ 文档上传成功: {file.filename} (字符数: {len(content)})"
        logging.info(success_msg)
        
        return jsonify({
            'success': True,
            'message': success_msg,
            'document': {
                'filename': file.filename,
                'file_size': doc_info['file_size'],
                'content_summary': content_summary,
                'upload_time': doc_info['upload_time']
            }
        })
        
    except Exception as e:
        logging.error(f"上传文档失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'上传失败: {str(e)}'}), 500


@app.route('/api/documents/<lesson_id>', methods=['GET'])
def get_documents(lesson_id):
    try:
        docs = uploaded_documents.get(lesson_id, [])
        return jsonify({
            'success': True,
            'documents': [
                {
                    'filename': doc['filename'],
                    'file_size': doc['file_size'],
                    'content_summary': doc['content_summary'],
                    'upload_time': doc['upload_time']
                }
                for doc in docs
            ]
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取文档列表失败: {str(e)}'}), 500


@app.route('/api/documents/<lesson_id>/<filename>', methods=['DELETE'])
def delete_document(lesson_id, filename):
    try:
        if lesson_id in uploaded_documents:
            docs = uploaded_documents[lesson_id]
            for i, doc in enumerate(docs):
                if doc['filename'] == filename:
                    if os.path.exists(doc['filepath']):
                        os.remove(doc['filepath'])
                    uploaded_documents[lesson_id].pop(i)
                    return jsonify({'success': True, 'message': '文档删除成功'})
        
        return jsonify({'success': False, 'message': '文档不存在'}), 404
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500


@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    try:
        return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)
    except Exception as e:
        return jsonify({'success': False, 'message': f'下载失败: {str(e)}'}), 404


@app.route('/api/download-template', methods=['GET'])
def download_template():
    """下载Excel模板"""
    try:
        output = create_lesson_plan_template()
        output.seek(0)
        # 使用RFC 5987编码中文文件名
        filename = '教案填写模板.xlsx'
        encoded_filename = quote(filename)
        return Response(
            output.getvalue(),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={
                'Content-Disposition': f"attachment; filename*=UTF-8''{encoded_filename}",
                'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }
        )
    except Exception as e:
        logging.error(f"生成模板失败: {str(e)}")
        return jsonify({'success': False, 'message': f'生成模板失败: {str(e)}'}), 500


@app.route('/api/upload-excel', methods=['POST'])
def upload_excel():
    """上传并解析Excel文件"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '没有上传文件'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'message': '文件名为空'}), 400
        
        if not file.filename.endswith('.xlsx'):
            return jsonify({'success': False, 'message': '请上传 .xlsx 格式的Excel文件'}), 400
        
        # 保存上传的文件
        temp_path = os.path.join(UPLOAD_DIR, f"temp_{int(time.time())}_{file.filename}")
        file.save(temp_path)
        
        # 解析Excel
        result = parse_lesson_plan_excel(temp_path)
        
        # 删除临时文件
        try:
            os.remove(temp_path)
        except:
            pass
        
        if result['success']:
            return jsonify({
                'success': True,
                'fixed_info': result['fixed_info'],
                'lessons': result['lessons'],
                'document_paths': result['document_paths'],
                'message': f"成功解析 {len(result['lessons'])} 个课时"
            })
        else:
            return jsonify({'success': False, 'message': result['error']}), 400
            
    except Exception as e:
        logging.error(f"解析Excel失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'解析失败: {str(e)}'}), 500


@app.route('/api/settings', methods=['GET'])
def get_llm_settings():
    """获取当前 LLM 配置信息（不返回完整 API Key）"""
    try:
        settings = load_settings_from_file()
        current_config = get_current_model_config() if 'get_current_model_config' in dir() else None

        return jsonify({
            'success': True,
            'settings': {
                'model_selection': settings.get('model_selection', 2),
                'model_name': settings.get('model_selection', 2) == 1 and 'MiniMax' or 'DeepSeek V3',
                'deepseek_api_key': mask_key(settings.get('deepseek_api_key', '')),
                'deepseek_api_url': settings.get('deepseek_api_url', 'https://api.deepseek.com/v1/chat/completions'),
                'minimax_api_key': mask_key(settings.get('minimax_api_key', '')),
                'minimax_api_url': settings.get('minimax_api_url', 'https://api.minimaxi.com/v1/chat/completions'),
                'is_configured': bool(settings.get('deepseek_api_key') or settings.get('minimax_api_key')),
                'api_key_configured': bool(settings.get('deepseek_api_key') or settings.get('minimax_api_key'))
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/settings', methods=['POST'])
def save_llm_settings():
    """保存 LLM 配置"""
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'message': '请提供配置参数'}), 400

        settings = {
            'model_selection': data.get('model_selection', 2),
            'deepseek_api_key': data.get('deepseek_api_key', ''),
            'deepseek_api_url': data.get('deepseek_api_url', 'https://api.deepseek.com/v1/chat/completions'),
            'minimax_api_key': data.get('minimax_api_key', ''),
            'minimax_api_url': data.get('minimax_api_url', 'https://api.minimaxi.com/v1/chat/completions'),
        }

        # 验证至少有一个 API Key
        if not settings['deepseek_api_key'] and not settings['minimax_api_key']:
            return jsonify({'success': False, 'message': '请至少填写一个模型的 API Key'}), 400

        save_settings_to_file(settings)
        reload_config()

        logging.info(f"LLM 配置已更新，当前使用: {'MiniMax' if settings['model_selection'] == 1 else 'DeepSeek V3'}")

        return jsonify({
            'success': True,
            'message': '配置保存成功',
            'model_name': 'MiniMax' if settings['model_selection'] == 1 else 'DeepSeek V3'
        })
    except Exception as e:
        logging.error(f"保存配置失败: {str(e)}")
        return jsonify({'success': False, 'message': f'保存失败: {str(e)}'}), 500


def mask_key(key):
    """遮蔽 API Key 中间部分"""
    if not key:
        return ''
    if len(key) <= 8:
        return '*' * len(key)
    return key[:4] + '*' * (len(key) - 8) + key[-4:]


@app.route('/setup')
def serve_setup_page():
    """提供 LLM 配置页面"""
    setup_path = os.path.join(STATIC_DIR, 'setup.html')
    if os.path.exists(setup_path):
        return send_from_directory(STATIC_DIR, 'setup.html')
    return '<h1>设置页面未找到</h1>', 404


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200


@app.route('/ping', methods=['GET'])
def ping():
    return 'pong', 200


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    if path and os.path.exists(os.path.join(STATIC_DIR, path)):
        return send_from_directory(STATIC_DIR, path)
    else:
        return send_from_directory(STATIC_DIR, 'index.html')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
