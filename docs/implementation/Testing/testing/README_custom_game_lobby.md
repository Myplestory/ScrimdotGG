# Custom Game Lobby Tester

This script tests setting up custom game lobbies with different NA servers using the `data.json` configuration and the `valclient` library.

## Features

- 🎯 **Server Selection**: Test different NA servers (Virginia, Illinois, Georgia)
- 🗺️ **Map Selection**: Choose from configured maps in data.json
- 🎮 **Interactive Mode**: User-friendly menu system
- 🧪 **Automated Testing**: Test all servers automatically
- ⚙️ **Custom Game Settings**: Full control over lobby configuration

## Prerequisites

1. **VALORANT Running**: Make sure VALORANT is running and you're logged in
2. **Python Dependencies**: The script uses the local `valclient` library
3. **data.json**: Configuration file with server and map preferences

## Usage

### Interactive Mode (Recommended)
```bash
cd server/testing
python test_custom_game_lobby.py
```

### Quick Test Mode
```bash
cd server/testing
python test_custom_game_lobby.py --quick
```

## Interactive Menu Options

1. **Create custom lobby (random server/map)** - Quick setup with random selections
2. **Create custom lobby (choose server)** - Select specific NA server
3. **Create custom lobby (choose map)** - Select specific map
4. **Create custom lobby (choose both)** - Select both server and map
5. **Test all servers** - Automatically test all configured NA servers
6. **Start current custom game** - Start the configured custom game
7. **Show current party info** - Display current lobby information
8. **Exit** - Close the application

## Configuration

The script reads configuration from `client/backend/data/data.json`:

```json
{
  "region": "na",
  "serverPreferences": {
    "North America": {
      "Virginia": "aresriot.aws-rclusterprod-use1-1.na-gp-ashburn-awsedge-1",
      "Illinois": "aresriot.aws-rclusterprod-use1-1.na-gp-chicago-awsedge-1",
      "Georgia": "aresriot.aws-atl2-prod.na-gp-atlanta-2"
    }
  },
  "mapPreferences": {
    "ascent": "/Game/Maps/Ascent/Ascent",
    "bind": "/Game/Maps/Duality/Duality",
    "breeze": "/Game/Maps/Foxtrot/Foxtrot",
    // ... more maps
  }
}
```

## Example Output

```
🎯 Custom Game Lobby Tester
==================================================
✅ Loaded configuration from /path/to/data.json
🔧 Initializing valclient for region: na
✅ Client initialized successfully
   Player: YourName#1234
   PUUID: 12345678-1234-1234-1234-123456789abc

🌎 Available NA servers:
   Virginia: aresriot.aws-rclusterprod-use1-1.na-gp-ashburn-awsedge-1
   Illinois: aresriot.aws-rclusterprod-use1-1.na-gp-chicago-awsedge-1
   Georgia: aresriot.aws-atl2-prod.na-gp-atlanta-2

🗺️  Available maps:
   ascent: /Game/Maps/Ascent/Ascent
   bind: /Game/Maps/Duality/Duality
   breeze: /Game/Maps/Foxtrot/Foxtrot
   // ... more maps

🎮 Interactive Custom Game Lobby Test
==================================================
```

## Troubleshooting

### Common Issues

1. **Handshake Error**: Make sure VALORANT is running and you're logged in
2. **File Not Found**: Ensure `data.json` exists in the correct location
3. **Invalid JSON**: Check that `data.json` has valid JSON syntax
4. **No Servers Configured**: Verify server preferences in `data.json`

### Error Messages

- `❌ Handshake error: Unable to activate; is VALORANT running?`
  - Solution: Start VALORANT and log in

- `❌ Error: Could not find data.json`
  - Solution: Check the file path in the script

- `❌ No NA servers configured in data.json`
  - Solution: Add server preferences to your configuration

## Technical Details

The script uses the following valclient methods:
- `Client()` - Initialize the client
- `activate()` - Authenticate with VALORANT
- `party_change_to_custom()` - Convert party to custom game
- `party_set_custom_game_settings()` - Configure lobby settings
- `party_start_custom_game()` - Start the custom game
- `fetch_party()` - Get current party information

## Server Information

The script supports these NA servers:
- **Virginia**: `aresriot.aws-rclusterprod-use1-1.na-gp-ashburn-awsedge-1`
- **Illinois**: `aresriot.aws-rclusterprod-use1-1.na-gp-chicago-awsedge-1`
- **Georgia**: `aresriot.aws-atl2-prod.na-gp-atlanta-2`
