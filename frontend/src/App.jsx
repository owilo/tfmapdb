import { Link } from 'react-router-dom'
import './App.css'

export default function App() {
  return (
    <div style={{ padding: '2rem' }}>
      <h1>Welcome to TFMap Entries</h1>
      <p>Use the URL <code>/map/&lt;id&gt;</code> to view an entry.</p>
      <p className="text-3xl font-bold underline">Hello world</p>
      <p>Example: <Link to="/map/7971698">@7971698</Link></p>
    </div>
  )
}