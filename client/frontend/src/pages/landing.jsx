import React from 'react';
import Layout from '../pages/layout'; // Adjust the path to where you placed Layout.jsx
import HomeComponent from '../components/home/home';
import Lobby from '../components/lobby/lobby';

const LandingPage = () => {
  const [activeComponent, setActiveComponent] = React.useState('home');

  return (
    <Layout setActiveComponent={setActiveComponent}>
      {activeComponent === 'home' && <HomeComponent />}
      {activeComponent === 'lobby' && <Lobby />}
    </Layout>
  );
};

export default LandingPage;
