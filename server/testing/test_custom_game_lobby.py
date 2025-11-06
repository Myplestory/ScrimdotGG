#!/usr/bin/env python3
"""
Test script for setting up custom game lobbies with different NA servers
using data.json configuration and valclient library.
"""

import json
import os
import sys
import time
import random
from pathlib import Path

# Add the server directory to the path to import valclient
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from valclient.client import Client
from valclient.exceptions import HandshakeError, ResponseError


class CustomGameLobbyTester:
    def __init__(self, data_json_path=None):
        """Initialize the tester with data.json configuration."""
        if data_json_path is None:
            # Default path to data.json
            data_json_path = os.path.join(
                os.path.dirname(__file__), 
                '..', '..', 'client', 'backend', 'data', 'data.json'
            )
        
        self.data_json_path = data_json_path
        self.config = self.load_config()
        self.client = None
        
    def load_config(self):
        """Load configuration from data.json."""
        try:
            with open(self.data_json_path, 'r') as f:
                config = json.load(f)
            print(f"✅ Loaded configuration from {self.data_json_path}")
            return config
        except FileNotFoundError:
            print(f"❌ Error: Could not find data.json at {self.data_json_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ Error: Invalid JSON in data.json: {e}")
            sys.exit(1)
    
    def initialize_client(self):
        """Initialize the valclient with the configured region."""
        try:
            region = self.config.get('region', 'na')
            print(f"🔧 Initializing valclient for region: {region}")
            
            self.client = Client(region=region)
            self.client.activate()
            
            print(f"✅ Client initialized successfully")
            print(f"   Player: {self.client.player_name}#{self.client.player_tag}")
            print(f"   PUUID: {self.client.puuid}")
            return True
            
        except HandshakeError as e:
            print(f"❌ Handshake error: {e}")
            print("   Make sure VALORANT is running and you're logged in!")
            return False
        except Exception as e:
            print(f"❌ Error initializing client: {e}")
            return False
    
    def get_available_servers(self):
        """Get available NA servers from configuration."""
        na_servers = self.config.get('serverPreferences', {}).get('North America', {})
        if not na_servers:
            print("❌ No NA servers configured in data.json")
            return {}
        
        print("🌎 Available NA servers:")
        for location, server_id in na_servers.items():
            print(f"   {location}: {server_id}")
        
        return na_servers
    
    def get_available_maps(self):
        """Get available maps from configuration."""
        maps = self.config.get('mapPreferences', {})
        if not maps:
            print("❌ No maps configured in data.json")
            return {}
        
        print("🗺️  Available maps:")
        for map_name, map_path in maps.items():
            print(f"   {map_name}: {map_path}")
        
        return maps
    
    def create_custom_game_lobby(self, server_location=None, map_name=None):
        """Create a custom game lobby with specified server and map."""
        if not self.client:
            print("❌ Client not initialized!")
            return False
        
        try:
            # Get available servers and maps
            servers = self.get_available_servers()
            maps = self.get_available_maps()
            
            if not servers:
                return False
            
            # Select server
            if server_location and server_location in servers:
                selected_server = servers[server_location]
                print(f"🎯 Using specified server: {server_location} ({selected_server})")
            else:
                # Random server selection
                server_location = random.choice(list(servers.keys()))
                selected_server = servers[server_location]
                print(f"🎲 Randomly selected server: {server_location} ({selected_server})")
            
            # Select map
            if map_name and map_name in maps:
                selected_map = maps[map_name]
                print(f"🗺️  Using specified map: {map_name} ({selected_map})")
            else:
                # Random map selection
                map_name = random.choice(list(maps.keys()))
                selected_map = maps[map_name]
                print(f"🎲 Randomly selected map: {map_name} ({selected_map})")
            
            # Get current party info
            print("📋 Fetching current party information...")
            party_info = self.client.fetch_party()
            print(f"   Current party ID: {party_info.get('ID', 'N/A')}")
            
            # Convert party to custom game
            print("🔄 Converting party to custom game...")
            self.client.party_change_to_custom()
            time.sleep(2)  # Wait for conversion
            
            # Set custom game settings
            custom_settings = {
                "Map": selected_map,
                "Mode": "/Game/GameModes/Bomb/BombGameMode.BombGameMode_C",
                "UseBots": False,
                "GamePod": selected_server,
                "GameRules": None
            }
            
            print("⚙️  Setting custom game settings...")
            print(f"   Map: {map_name}")
            print(f"   Server: {server_location}")
            print(f"   Mode: Bomb (Standard)")
            
            self.client.party_set_custom_game_settings(custom_settings)
            time.sleep(2)  # Wait for settings to apply
            
            # Verify settings were applied
            updated_party = self.client.fetch_party()
            custom_game_settings = updated_party.get('CustomGameSettings', {})
            
            print("✅ Custom game lobby created successfully!")
            print(f"   Party ID: {updated_party.get('ID', 'N/A')}")
            print(f"   Map: {custom_game_settings.get('Map', 'N/A')}")
            print(f"   Server: {custom_game_settings.get('GamePod', 'N/A')}")
            print(f"   Mode: {custom_game_settings.get('Mode', 'N/A')}")
            
            return True
            
        except ResponseError as e:
            print(f"❌ Response error: {e}")
            return False
        except Exception as e:
            print(f"❌ Error creating custom game lobby: {e}")
            return False
    
    def start_custom_game(self):
        """Start the custom game."""
        if not self.client:
            print("❌ Client not initialized!")
            return False
        
        try:
            print("🚀 Starting custom game...")
            result = self.client.party_start_custom_game()
            print("✅ Custom game started successfully!")
            return True
            
        except ResponseError as e:
            print(f"❌ Response error starting game: {e}")
            return False
        except Exception as e:
            print(f"❌ Error starting custom game: {e}")
            return False
    
    def test_multiple_servers(self):
        """Test creating lobbies on different NA servers."""
        servers = self.get_available_servers()
        if not servers:
            return False
        
        print("\n🧪 Testing multiple servers...")
        results = {}
        
        for server_location in servers:
            print(f"\n--- Testing {server_location} ---")
            success = self.create_custom_game_lobby(server_location=server_location)
            results[server_location] = success
            
            if success:
                print(f"✅ {server_location} test passed")
                # Wait a bit before testing next server
                time.sleep(3)
            else:
                print(f"❌ {server_location} test failed")
        
        # Summary
        print("\n📊 Test Results Summary:")
        for server, success in results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"   {server}: {status}")
        
        return results
    
    def run_interactive_test(self):
        """Run an interactive test session."""
        print("\n🎮 Interactive Custom Game Lobby Test")
        print("=" * 50)
        
        while True:
            print("\nOptions:")
            print("1. Create custom lobby (random server/map)")
            print("2. Create custom lobby (choose server)")
            print("3. Create custom lobby (choose map)")
            print("4. Create custom lobby (choose both)")
            print("5. Test all servers")
            print("6. Start current custom game")
            print("7. Show current party info")
            print("8. Exit")
            
            choice = input("\nEnter your choice (1-8): ").strip()
            
            if choice == '1':
                self.create_custom_game_lobby()
            elif choice == '2':
                servers = self.get_available_servers()
                if servers:
                    print("\nAvailable servers:")
                    for i, server in enumerate(servers.keys(), 1):
                        print(f"{i}. {server}")
                    try:
                        server_choice = int(input("Choose server (number): ")) - 1
                        server_name = list(servers.keys())[server_choice]
                        self.create_custom_game_lobby(server_location=server_name)
                    except (ValueError, IndexError):
                        print("❌ Invalid choice")
            elif choice == '3':
                maps = self.get_available_maps()
                if maps:
                    print("\nAvailable maps:")
                    for i, map_name in enumerate(maps.keys(), 1):
                        print(f"{i}. {map_name}")
                    try:
                        map_choice = int(input("Choose map (number): ")) - 1
                        map_name = list(maps.keys())[map_choice]
                        self.create_custom_game_lobby(map_name=map_name)
                    except (ValueError, IndexError):
                        print("❌ Invalid choice")
            elif choice == '4':
                servers = self.get_available_servers()
                maps = self.get_available_maps()
                if servers and maps:
                    print("\nAvailable servers:")
                    for i, server in enumerate(servers.keys(), 1):
                        print(f"{i}. {server}")
                    try:
                        server_choice = int(input("Choose server (number): ")) - 1
                        server_name = list(servers.keys())[server_choice]
                        
                        print("\nAvailable maps:")
                        for i, map_name in enumerate(maps.keys(), 1):
                            print(f"{i}. {map_name}")
                        map_choice = int(input("Choose map (number): ")) - 1
                        map_name = list(maps.keys())[map_choice]
                        
                        self.create_custom_game_lobby(server_location=server_name, map_name=map_name)
                    except (ValueError, IndexError):
                        print("❌ Invalid choice")
            elif choice == '5':
                self.test_multiple_servers()
            elif choice == '6':
                self.start_custom_game()
            elif choice == '7':
                if self.client:
                    try:
                        party_info = self.client.fetch_party()
                        print(f"\n📋 Current Party Info:")
                        print(f"   ID: {party_info.get('ID', 'N/A')}")
                        print(f"   State: {party_info.get('State', 'N/A')}")
                        print(f"   Accessibility: {party_info.get('Accessibility', 'N/A')}")
                        custom_settings = party_info.get('CustomGameSettings', {})
                        if custom_settings:
                            print(f"   Custom Game Settings:")
                            print(f"     Map: {custom_settings.get('Map', 'N/A')}")
                            print(f"     Server: {custom_settings.get('GamePod', 'N/A')}")
                            print(f"     Mode: {custom_settings.get('Mode', 'N/A')}")
                    except Exception as e:
                        print(f"❌ Error fetching party info: {e}")
                else:
                    print("❌ Client not initialized")
            elif choice == '8':
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice, please try again")


def main():
    """Main function to run the test script."""
    print("🎯 Custom Game Lobby Tester")
    print("=" * 50)
    
    # Initialize tester
    tester = CustomGameLobbyTester()
    
    # Initialize client
    if not tester.initialize_client():
        print("❌ Failed to initialize client. Exiting.")
        return
    
    # Check if we should run interactive mode or quick test
    if len(sys.argv) > 1 and sys.argv[1] == '--quick':
        print("\n🏃 Running quick test...")
        # Quick test with random server and map
        success = tester.create_custom_game_lobby()
        if success:
            print("✅ Quick test completed successfully!")
        else:
            print("❌ Quick test failed!")
    else:
        # Interactive mode
        tester.run_interactive_test()


if __name__ == "__main__":
    main()
