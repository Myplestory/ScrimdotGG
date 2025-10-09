import { useState, useEffect } from 'react';
import { w3cwebsocket as W3CWebSocket } from 'websocket';

const client = new W3CWebSocket('ws://localhost:8000');

const MatchAcceptancePopup = ({ onClose }) => {
  const [timeLeft, setTimeLeft] = useState(30); // example: 30 seconds to accept

  useEffect(() => {
    const timer = setTimeout(() => {
      if (timeLeft > 0) setTimeLeft(timeLeft - 1);
      else onClose(false); // auto-decline after time expires
    }, 1000);

    return () => clearTimeout(timer);
  }, [timeLeft, onClose]);

  const handleAccept = () => {
    client.send(JSON.stringify({ action: 'accept_match', match_id: '123' }));
    onClose(true);
  };

  return (
    <div>
      <p>Match found! Accept?</p>
      <p>{timeLeft} seconds remaining</p>
      <button onClick={handleAccept}>Accept</button>
      <button onClick={() => onClose(false)}>Decline</button>
    </div>
  );
};

export default MatchAcceptancePopup;
