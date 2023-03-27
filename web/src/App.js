import './App.css';
import React, {useEffect, useState} from "react";
import {Container, Button, Typography, Grid} from '@mui/material';


function App() {
  const [text, setText] = useState('');
  const [webSocket, setWebSocket] = useState(null);

  useEffect(() => {
    const socket = new WebSocket('ws://localhost:8000');

    socket.addEventListener('message', event => {
      console.log(event)
      const jsonPayload = JSON.parse(event.data)
      if (jsonPayload.event === 'text_update') {
        setText(jsonPayload.text);
      }
    });

    setWebSocket(socket);

    return () => {
      socket.close();
    };
  }, []);
  const handleSpeak = () => {
    if (text) {
      const payload = {
        "event": "speak", text,
      }
      webSocket.send(JSON.stringify(payload))
      setText("")
    }
  }

  const handleReset = () => {
    setText("")
  }

  return (
    <Container maxWidth="lg">
      <div id="text-container">
        <Typography variant="body1" component="body1">
          {text || 'Waiting for some response...'}
        </Typography>
      </div>
      <Grid id="button-container" container spacing={2}>
        <Button
          variant="contained"
          onClick={handleSpeak}>Speak</Button>
        <Button
          variant="contained"
          onClick={handleReset}>Reset</Button>
      </Grid>
    </Container>
  );
}

export default App;
