"""
Migration Script: Update Existing Players to New MMR/ELO System
Run this after applying database migrations to set MMR values for existing players.
"""

import os
import sys
import django

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scrimgg.settings')
django.setup()

from scrimgg.models import Player
from matchmaking.trueskill_manager import mmr_to_trueskill_mu


def migrate_players():
    """
    Migrate existing players to the new MMR/ELO system.
    
    Strategy:
    1. Keep existing ELO (display rank)
    2. Estimate MMR based on current ELO
    3. Set TrueSkill components
    4. Mark all as settled (since they have game history)
    """
    print("="*70)
    print("  MIGRATING EXISTING PLAYERS TO MMR/ELO SYSTEM")
    print("="*70)
    
    players = Player.objects.all()
    total_count = players.count()
    
    print(f"\nFound {total_count} players to migrate\n")
    
    if total_count == 0:
        print("[INFO] No players to migrate")
        return
    
    # Ask for confirmation
    print("Migration Strategy:")
    print("  1. Keep existing Display ELO (unchanged)")
    print("  2. Estimate MMR from current ELO:")
    print("     - If ELO > 4000: MMR = ELO x 0.95 (slightly deflate)")
    print("     - If ELO <= 4000: MMR = ELO x 1.05 (slightly inflate)")
    print("  3. Set TrueSkill components based on MMR")
    print("  4. Mark as settled (sigma = 2.5, moderate confidence)")
    print("  5. Set games_played = 50 (simulated history)")
    print("\nThis preserves their current rank while initializing MMR.\n")
    
    choice = input("Proceed with migration? (yes/no): ")
    if choice.lower() != 'yes':
        print("Migration cancelled")
        return
    
    print("\nMigrating players...\n")
    
    migrated_count = 0
    
    for player in players:
        try:
            old_elo = player.elo
            
            # Estimate MMR based on current ELO
            if player.elo > 4000:
                # Higher ELO players: slightly deflate MMR
                estimated_mmr = player.elo * 0.95
            else:
                # Lower ELO players: slightly inflate MMR
                estimated_mmr = player.elo * 1.05
            
            # Convert to TrueSkill mu
            trueskill_mu = mmr_to_trueskill_mu(estimated_mmr)
            
            # Set as settled with moderate confidence
            trueskill_sigma = 2.5  # Already settled, moderate confidence
            
            # Update player
            player.mmr = estimated_mmr
            player.trueskill_mu = trueskill_mu
            player.trueskill_sigma = trueskill_sigma
            player.games_played = 50  # Simulated game history
            player.is_in_placement = False  # Not in placement
            player.is_settled = True  # Already settled
            player.last_game_timestamp = 0.0  # Will be set on next game
            
            player.save()
            
            migrated_count += 1
            
            if migrated_count % 10 == 0:
                print(f"  Migrated {migrated_count}/{total_count} players...")
            
            # Print first few for verification
            if migrated_count <= 3:
                print(f"  [{migrated_count}] {player.alias}:")
                print(f"      Display ELO: {old_elo} (unchanged)")
                print(f"      Estimated MMR: {estimated_mmr:.0f}")
                print(f"      TrueSkill: mu={trueskill_mu:.2f}, sigma={trueskill_sigma:.2f}")
                print(f"      Games: 50, Settled: True")
        
        except Exception as e:
            print(f"  [ERROR] Failed to migrate {player.alias}: {e}")
    
    print(f"\n[OK] Successfully migrated {migrated_count}/{total_count} players!")
    print("\nMigration Summary:")
    print(f"  Total players: {total_count}")
    print(f"  Migrated: {migrated_count}")
    print(f"  Failed: {total_count - migrated_count}")
    print("\nAll players now have MMR, TrueSkill, and activity tracking!\n")


def verify_migration():
    """Verify migration was successful"""
    print("="*70)
    print("  VERIFYING MIGRATION")
    print("="*70)
    
    players = Player.objects.all()
    
    # Check for any null values
    issues = []
    
    for player in players:
        if player.mmr is None or player.mmr == 0:
            issues.append(f"{player.alias}: MMR is null/zero")
        if player.trueskill_mu is None or player.trueskill_mu == 0:
            issues.append(f"{player.alias}: TrueSkill mu is null/zero")
        if player.trueskill_sigma is None or player.trueskill_sigma == 0:
            issues.append(f"{player.alias}: TrueSkill sigma is null/zero")
    
    if issues:
        print("\n[FAIL] Found issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("\n[OK] All players have valid MMR and TrueSkill data!")
        
        # Print sample
        sample = players[:5]
        print(f"\nSample of {len(sample)} players:")
        for p in sample:
            print(f"  {p.alias}:")
            print(f"    Display ELO: {p.elo}")
            print(f"    Hidden MMR: {p.mmr:.0f}")
            print(f"    TrueSkill: mu={p.trueskill_mu:.2f}, sigma={p.trueskill_sigma:.2f}")
            print(f"    Gap: {abs(p.mmr - p.elo):.0f}")
        
        return True


def main():
    """Main migration script"""
    try:
        migrate_players()
        
        print("\nVerifying migration...")
        verified = verify_migration()
        
        if verified:
            print("\n" + "="*70)
            print("  MIGRATION COMPLETE!")
            print("="*70)
            print("\nNext steps:")
            print("  1. Test matchmaking with new system")
            print("  2. Update bot creation scripts to use new defaults")
            print("  3. Monitor player convergence over time")
            print("\n")
        else:
            print("\n[ERROR] Migration verification failed. Please review errors above.")
    
    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

