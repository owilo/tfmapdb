import { Link } from 'react-router-dom'
import 'App.css'

export default function App() {
  return (
    <div style={{ padding: '2rem' }}>
      <h1>Welcome to TFMap Entries</h1>
      <p>Use the URL <code>/entry/&lt;id&gt;</code> to view an entry.</p>
      <p>Example: <Link to="/entry/1">/entry/1</Link></p>
    </div>
  )
}