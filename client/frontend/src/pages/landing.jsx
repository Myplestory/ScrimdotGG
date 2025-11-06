import React from 'react';
import { useLocation } from 'react-router-dom';
import HomeComponent from '../components/home/home';
import Lobby from '../components/lobby/lobby';
import Play from './matchmake/play';

const LandingPage = () => {
  const location = useLocation();
  const initialComponent = location.state?.activeComponent || 'home';
  const [activeComponent, setActiveComponent] = React.useState(initialComponent);

  // Update activeComponent when location state changes
  React.useEffect(() => {
    if (location.state?.activeComponent) {
      setActiveComponent(location.state.activeComponent);
    }
  }, [location.state?.activeComponent]);

  return (
    <>
      {activeComponent === 'home' && <HomeComponent />}
      {activeComponent === 'lobby' && <Lobby />}
      {activeComponent === 'pug' && <Play />}
    </>
  );
};

export default LandingPage;
