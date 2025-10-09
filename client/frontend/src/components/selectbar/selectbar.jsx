import React, { useState } from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import MapIcon from '@mui/icons-material/Map';
import LanguageIcon from '@mui/icons-material/Language';
import Modal from '@mui/material/Modal';
import ButtonBase from '@mui/material/ButtonBase';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import CloseIcon from '@mui/icons-material/Close';
import { FormGroup, FormControlLabel, Checkbox, styled } from '@mui/material';

const StyledFormGroup = styled(FormGroup)(({ theme }) => ({
  display: 'flex',
}));

function HorizontalBox( {selectedMaps, setSelectedMaps, selectedServers, setSelectedServers} ) {
  const [isServerModalOpen, setServerModalOpen] = useState(false);
  const [isMapModalOpen, setMapModalOpen] = useState(false);
  const [tempSelectedMaps, setTempSelectedMaps] = useState(selectedMaps);
  const [tempSelectedServers, setTempSelectedServers] = useState(selectedServers);
  const handleServerModalOpen = () => setServerModalOpen(true);
  const handleServerModalClose = () => {
    setSelectedServers(tempSelectedServers); // Confirm selections
    setServerModalOpen(false);
  };
  const handleServerSelectionChange = (event) => {
    const serverName = event.target.name;
    const isChecked = event.target.checked;
    setTempSelectedServers(
      isChecked
        ? [...tempSelectedServers, serverName]
        : tempSelectedServers.filter((server) => server !== serverName)
    );
  };

  const handleMapModalOpen = () => setMapModalOpen(true);
  const handleMapModalClose = () => {
    setSelectedMaps(tempSelectedMaps); // Confirm selections
    setMapModalOpen(false);
  };
  const handleMapSelectionChange = (event) => {
    const mapName = event.target.name;
    const isChecked = event.target.checked;
    setTempSelectedMaps(
      isChecked
        ? [...tempSelectedMaps, mapName]
        : tempSelectedMaps.filter((map) => map !== mapName)
    );
  };

  const modalStyle = {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    width: 400,
    bgcolor: 'background.paper',
    boxShadow: 24,
    p: 4,
    borderRadius: 2,
    bgcolor: 'rgba(77, 77, 77, 0.95)', 
  };

  // Define the modal body content as a reusable component if needed
  const ServerModalBody = (
    <Box sx={modalStyle}>
      {/* Modal Close Button */}
      <IconButton
        aria-label="close"
        onClick={handleServerModalClose}
        sx={{
          position: 'absolute',
          right: 8,
          top: 8,
        }}
      >
      <CloseIcon />
      </IconButton>
      <Typography variant="h6" component="h2" sx={{ mb: 2 }}>
      </Typography>
      <StyledFormGroup>
        {["portland", "san Jose", "dallas", "atlanta", "ashburn", "chicago"].map((serverName) => (
          <FormControlLabel
            key={serverName}
            control={<Checkbox checked={tempSelectedServers.includes(serverName)} onChange={handleServerSelectionChange} name={serverName} />}
            label={serverName}
          />
        ))}
      </StyledFormGroup>
    </Box>
  );

  const MapModalBody = (
    <Box sx={modalStyle}>
      {/* Modal Close Button */}
      <IconButton
        aria-label="close"
        onClick={handleMapModalClose}
        sx={{
          position: 'absolute',
          right: 8,
          top: 8,
        }}
      >
        <CloseIcon />
      </IconButton>
      <Typography variant="h6" component="h2" sx={{ mb: 2 }}>
        Choose Maps
      </Typography>
      {/* Map Form Content */}
      <FormGroup>
        {["ascent", "bind", "breeze", "split", "haven", "icebox", "lotus", "fracture", "pearl", "sunset"].map((mapName) => (
          <FormControlLabel
            key={mapName}
            control={<Checkbox checked={tempSelectedMaps.includes(mapName)} onChange={handleMapSelectionChange} name={mapName} />}
            label={mapName}
          />
        ))}
      </FormGroup>
    </Box>
  );

  return (
    <Box
          sx={{
            display: 'flex',          // Use flexbox layout
            flexDirection: 'row',     // Arrange children in a row
            alignItems: 'center',     // Vertically align items in the center
            justifyContent: 'flex-start',
            width: '100%',            // Take up the full width of the parent (adjusted to 100%)
            maxWidth: '700px',
            height: '50px',
            flex: 1,
            p: 1,                     // Add some padding around the box
            bgcolor: 'background.paper', // Use theme's background color for paper
            boxShadow: 1,             // Apply box shadow for some depth (optional)
            borderRadius: 1           // Round the corners (optional)
          }}
        >
      {/* Server Clickable Area */}
      <ButtonBase onClick={handleServerModalOpen} sx={{ display: 'flex', alignItems: 'center', marginRight: '30%' }}>
        <LanguageIcon sx={{ marginLeft: '10%' }} />
        <Typography variant="body1" sx={{ marginLeft: '8px' }}>
          Servers
        </Typography>
      </ButtonBase>

      {/* Map Clickable Area */}
      <ButtonBase onClick={handleMapModalOpen} sx={{ display: 'flex', alignItems: 'center' }}>
        <MapIcon sx={{ marginLeft: '2%' }} />
        <Typography variant="body1" sx={{ marginLeft: '8px' }}>
          Maps
        </Typography>
      </ButtonBase>

      {/* Server Modal */}
      <Modal
        open={isServerModalOpen}
        onClose={handleServerModalClose}
        aria-labelledby="server-modal-title"
        aria-describedby="server-modal-description"
      >
        {ServerModalBody}
      </Modal>

      {/* Map Modal */}
      <Modal
        open={isMapModalOpen}
        onClose={handleMapModalClose}
        aria-labelledby="map-modal-title"
        aria-describedby="map-modal-description"
      >
        {MapModalBody}
      </Modal>
    </Box>
  );
}

export default HorizontalBox;