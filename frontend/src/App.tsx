function App() {
  return (
    <div style={{ 
      textAlign: 'center', 
      paddingTop: '30vh',
      fontFamily: 'sans-serif'
    }}>
      <h1 style={{ fontSize: 48, color: '#1677ff' }}>Hello World</h1>
      <p style={{ fontSize: 20, color: '#666' }}>
        公网穿透测试成功 ✅
      </p>
      <p style={{ color: '#999' }}>
        {new Date().toLocaleString('zh-CN')}
      </p>
    </div>
  )
}

export default App
