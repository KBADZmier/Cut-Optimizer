import { useState } from 'react'
import './App.css'

function App() {
  const [count, setCount] = useState(0)
  const [height, setheight] = useState(0)
  const [width, setwidth] = useState(0)
  const [lenghtP, setlenghtP] = useState(0)
  const [okap, setOkap] = useState(false)
  return (
    <>
      <section id="center">
        <div>
          <h1>Moskitiery</h1>
        </div>
  
      </section>

      <div className="ticks"></div>

    </>
  )
}

export default App
