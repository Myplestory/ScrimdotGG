# 🤖 Veto Bot Implementation Draft

## Overview
This document outlines the implementation strategy for bot veto simulation in the matchmaking system. The bots will simulate realistic veto behavior during the map selection phase.

## Current System Status
- ✅ V4 Bot System: Working perfectly with WebSocket connections
- ✅ Match Creation: All 10 players accept matches successfully
- ✅ Veto Phase: Backend transitions to VETO state correctly
- ❌ Bot Veto Simulation: Not yet implemented

## Implementation Plan

### Phase 1: Bot Veto Event Handling

```python
# In test_queue_with_bots_v4.py - Add veto event handlers

class BotVetoSimulator:
    def __init__(self, bot_client):
        self.bot_client = bot_client
        self.is_captain = False
        self.my_team = None
        self.available_maps = []
        self.vetoed_maps = []
        self.current_turn = None
        self.veto_deadline = None
        
    async def handle_veto_events(self):
        """Handle all veto-related WebSocket events"""
        
        # Listen for veto_started event
        await self.bot_client.on('veto_started', self.on_veto_started)
        
        # Listen for veto_update events (map vetoed, turn changes)
        await self.bot_client.on('veto_update', self.on_veto_update)
        
        # Listen for veto_complete event
        await self.bot_client.on('veto_complete', self.on_veto_complete)
        
        # Listen for veto_timeout events
        await self.bot_client.on('veto_timeout', self.on_veto_timeout)
```

### Phase 2: Veto Decision Logic

```python
class VetoStrategy:
    """Different veto strategies for bots"""
    
    @staticmethod
    def random_veto(available_maps):
        """Randomly select a map to veto"""
        return random.choice(available_maps)
    
    @staticmethod
    def strategic_veto(available_maps, team_preference=None):
        """Strategic veto based on team preferences"""
        # Could implement map preferences, team strengths, etc.
        if team_preference:
            # Avoid maps the team is weak on
            pass
        return random.choice(available_maps)
    
    @staticmethod
    def aggressive_veto(available_maps):
        """Always veto the most popular/strongest maps"""
        # Priority order: Haven, Bind, Ascent, Split, etc.
        priority_maps = ['Haven', 'Bind', 'Ascent', 'Split', 'Icebox', 'Breeze', 'Fracture']
        
        for map_name in priority_maps:
            if map_name in available_maps:
                return map_name
        
        return random.choice(available_maps)
```

### Phase 3: Bot Veto Behavior

```python
async def on_veto_started(self, data):
    """Handle veto phase start"""
    logger.info(f"🎮 [{self.bot_client.alias}] Veto phase started!")
    
    self.available_maps = data.get('available_maps', [])
    self.current_turn = data.get('current_turn')
    self.veto_deadline = data.get('veto_deadline')
    
    # Determine if this bot is captain
    self.is_captain = data.get('is_captain', False)
    self.my_team = data.get('my_team')
    
    logger.info(f"   Available maps: {self.available_maps}")
    logger.info(f"   Current turn: {self.current_turn}")
    logger.info(f"   I am captain: {self.is_captain}")
    logger.info(f"   My team: {self.my_team}")
    
    # If it's my turn and I'm captain, make a veto decision
    if self.is_captain and self.current_turn == self.my_team:
        await self.make_veto_decision()

async def on_veto_update(self, data):
    """Handle veto updates (map vetoed, turn changes)"""
    logger.info(f"🎮 [{self.bot_client.alias}] Veto update received")
    
    self.available_maps = data.get('remaining_maps', [])
    self.vetoed_maps = data.get('vetoed_maps', [])
    self.current_turn = data.get('veto_turn')
    self.veto_deadline = data.get('veto_deadline')
    
    logger.info(f"   Remaining maps: {self.available_maps}")
    logger.info(f"   Vetoed maps: {self.vetoed_maps}")
    logger.info(f"   Current turn: {self.current_turn}")
    
    # If it's my turn and I'm captain, make a veto decision
    if self.is_captain and self.current_turn == self.my_team:
        await self.make_veto_decision()

async def make_veto_decision(self):
    """Make a veto decision when it's the bot's turn"""
    if not self.available_maps:
        logger.warning(f"⚠️ [{self.bot_client.alias}] No maps available to veto!")
        return
    
    # Choose veto strategy based on bot personality
    strategy = getattr(self.bot_client, 'veto_strategy', 'random')
    
    if strategy == 'strategic':
        map_to_veto = VetoStrategy.strategic_veto(self.available_maps)
    elif strategy == 'aggressive':
        map_to_veto = VetoStrategy.aggressive_veto(self.available_maps)
    else:
        map_to_veto = VetoStrategy.random_veto(self.available_maps)
    
    logger.info(f"🗺️ [{self.bot_client.alias}] Vetoing map: {map_to_veto}")
    
    # Send veto action
    await self.bot_client.send_event('veto_map', {
        'match_id': self.bot_client.current_match_id,
        'map_name': map_to_veto,
        'action_type': 'ban'
    })
```

### Phase 4: Bot Personality System

```python
class BotPersonality:
    """Different bot personalities for varied veto behavior"""
    
    @staticmethod
    def create_bot_personalities():
        return {
            'aggressive': {
                'veto_strategy': 'aggressive',
                'veto_delay': (1, 3),  # 1-3 second delay
                'description': 'Always vetoes strong maps'
            },
            'strategic': {
                'veto_strategy': 'strategic', 
                'veto_delay': (2, 5),  # 2-5 second delay
                'description': 'Makes strategic veto decisions'
            },
            'random': {
                'veto_strategy': 'random',
                'veto_delay': (1, 4),  # 1-4 second delay
                'description': 'Random veto decisions'
            },
            'slow': {
                'veto_strategy': 'random',
                'veto_delay': (5, 10),  # 5-10 second delay
                'description': 'Takes time to make decisions'
            }
        }

# Assign personalities to bots
async def create_bots_with_personalities():
    personalities = BotPersonality.create_bot_personalities()
    personality_names = list(personalities.keys())
    
    bots = []
    for i in range(10):
        personality = random.choice(personality_names)
        bot = await create_bot_with_personality(f"QueueBot{i}", personality)
        bots.append(bot)
    
    return bots
```

### Phase 5: Veto Testing Scenarios

```python
class VetoTestScenarios:
    """Different test scenarios for veto phase"""
    
    @staticmethod
    async def test_normal_veto_flow():
        """Test normal veto flow with all bots participating"""
        logger.info("🧪 Testing normal veto flow...")
        
        # Create 10 bots with different personalities
        bots = await create_bots_with_personalities()
        
        # Start matchmaking
        await start_matchmaking_with_bots(bots)
        
        # Wait for match creation and veto phase
        await wait_for_veto_phase()
        
        # Monitor veto progress
        await monitor_veto_progress()
        
        # Verify final map selection
        await verify_final_map()
    
    @staticmethod
    async def test_veto_timeout_scenario():
        """Test veto timeout when bot doesn't respond"""
        logger.info("🧪 Testing veto timeout scenario...")
        
        # Create 9 normal bots + 1 unresponsive bot
        bots = await create_bots_with_personalities()
        unresponsive_bot = await create_unresponsive_bot("TimeoutBot")
        
        # Start matchmaking
        await start_matchmaking_with_bots(bots + [unresponsive_bot])
        
        # Wait for veto phase
        await wait_for_veto_phase()
        
        # Verify timeout handling
        await verify_veto_timeout_handling()
    
    @staticmethod
    async def test_captain_disconnect_scenario():
        """Test when captain disconnects during veto"""
        logger.info("🧪 Testing captain disconnect scenario...")
        
        # Create bots and start match
        bots = await create_bots_with_personalities()
        await start_matchmaking_with_bots(bots)
        await wait_for_veto_phase()
        
        # Disconnect captain during veto
        captain_bot = find_captain_bot(bots)
        await captain_bot.disconnect()
        
        # Verify system handles captain disconnect
        await verify_captain_disconnect_handling()
```

### Phase 6: Veto Monitoring & Logging

```python
class VetoMonitor:
    """Monitor veto phase progress and log detailed information"""
    
    def __init__(self):
        self.veto_history = []
        self.start_time = None
        self.end_time = None
    
    async def log_veto_action(self, bot_name, action, map_name, team):
        """Log individual veto actions"""
        timestamp = datetime.now()
        self.veto_history.append({
            'timestamp': timestamp,
            'bot': bot_name,
            'action': action,
            'map': map_name,
            'team': team
        })
        
        logger.info(f"📝 VETO ACTION: {bot_name} ({team}) {action} {map_name}")
    
    async def log_veto_progress(self, available_maps, vetoed_maps, current_turn):
        """Log overall veto progress"""
        logger.info(f"📊 VETO PROGRESS:")
        logger.info(f"   Available: {available_maps}")
        logger.info(f"   Vetoed: {vetoed_maps}")
        logger.info(f"   Current turn: {current_turn}")
        logger.info(f"   Remaining: {len(available_maps)} maps")
    
    async def generate_veto_report(self):
        """Generate final veto phase report"""
        duration = (self.end_time - self.start_time).total_seconds()
        
        logger.info("📋 VETO PHASE REPORT:")
        logger.info(f"   Duration: {duration:.2f} seconds")
        logger.info(f"   Total actions: {len(self.veto_history)}")
        logger.info(f"   Actions by team:")
        
        team_a_actions = [a for a in self.veto_history if a['team'] == 'team_a']
        team_b_actions = [a for a in self.veto_history if a['team'] == 'team_b']
        
        logger.info(f"     Team A: {len(team_a_actions)} actions")
        logger.info(f"     Team B: {len(team_b_actions)} actions")
        
        for action in self.veto_history:
            logger.info(f"     {action['timestamp'].strftime('%H:%M:%S')} - {action['bot']} ({action['team']}) {action['action']} {action['map']}")
```

## Implementation Steps

1. **Extend Bot Client**: Add veto event handlers to existing bot WebSocket client
2. **Add Veto Logic**: Implement veto decision-making algorithms
3. **Personality System**: Create different bot personalities for varied behavior
4. **Testing Scenarios**: Implement comprehensive veto testing scenarios
5. **Monitoring**: Add detailed logging and progress tracking
6. **Integration**: Integrate with existing V4 bot system

## Key Features

- ✅ **Realistic Behavior**: Bots make decisions with human-like delays
- ✅ **Varied Strategies**: Different veto strategies (aggressive, strategic, random)
- ✅ **Error Handling**: Test timeout scenarios and edge cases
- ✅ **Comprehensive Logging**: Detailed veto phase monitoring
- ✅ **Easy Testing**: Simple test scenarios for different situations

## Files to Modify

1. **`server/testing/test_queue_with_bots_v4.py`** - Main bot implementation
2. **`server/testing/bot_websocket_client.py`** - WebSocket client extensions
3. **New files**: `veto_simulator.py`, `veto_strategies.py`, `veto_monitor.py`

## Testing Commands

```bash
# Test normal veto flow
python server/testing/test_veto_flow.py --scenario normal

# Test veto timeout
python server/testing/test_veto_flow.py --scenario timeout

# Test captain disconnect
python server/testing/test_veto_flow.py --scenario disconnect

# Run all veto tests
python server/testing/test_veto_flow.py --scenario all
```

## Expected Results

After implementation, the bots will:
- ✅ Automatically participate in veto phase
- ✅ Make realistic veto decisions with delays
- ✅ Handle timeouts and edge cases
- ✅ Provide comprehensive logging
- ✅ Test all veto system functionality

This will create a robust bot system that can fully simulate the veto phase, allowing comprehensive testing of the veto system including normal flow, timeouts, disconnections, and edge cases!
