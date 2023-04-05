import './App.css';
import React, {useState} from "react";
import {Container, Button, Typography, Grid, TextField} from '@mui/material';
import useWebSocket from "react-use-websocket";


function App() {
  const [text, setText] = useState('');
  const [webSocketUrl, setSocketURL] = useState('localhost:8000')
  const {
    sendJsonMessage
  } = useWebSocket(`ws://${webSocketUrl}`, {
    onOpen: () => {
      sendJsonMessage({
        event: "connected"
      })
    },
    //Will attempt to reconnect on all close events, such as server shutting down
    shouldReconnect: (closeEvent) => true,
    onMessage: (messageEvent) => {
      console.log(messageEvent)
      const jsonPayload = JSON.parse(messageEvent.data)
      if (jsonPayload.event === 'text_update') {
        setText(jsonPayload.message);
      }
    }
  });


  const handleSpeak = () => {
    if (text) {
      const payload = {
        "event": "speak", text,
      }
      sendJsonMessage(payload)
      setText("")
    }
  }

  const handleReset = () => {
    setText("")
  }

  return (
    <Container maxWidth="lg">
      <Grid style={{
        display: 'flex',
        alignItems: 'center',

      }}>
        <TextField
          size="small"
          onChange={(event) => {
            setSocketURL(event.target.value)
          }}
          value={webSocketUrl}></TextField>
        <Button style={{margin: 5}} size="small" variant="contained">Switch socket</Button>
      </Grid>
      <div id="text-container">
        <Typography variant="body1">
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
