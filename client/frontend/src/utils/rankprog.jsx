const getRankAndProgress = (elo) => {
  const ranks = [
    { min: 7500, max: Infinity, rank: 'S' },
    { min: 6250, max: 7499, rank: 'G' },
    { min: 5500, max: 6249, rank: 'A+' },
    { min: 5000, max: 5499, rank: 'A' },
    { min: 4500, max: 4999, rank: 'A-' },
    { min: 4000, max: 4499, rank: 'B+' },
    { min: 3500, max: 3999, rank: 'B' },
    { min: 3000, max: 3499, rank: 'B-' },
    { min: 2500, max: 2999, rank: 'C+' },
    { min: 2000, max: 2499, rank: 'C' },
    { min: 1500, max: 1999, rank: 'C-' },
    { min: 1000, max: 1499, rank: 'D+' },
    { min: 500, max: 999, rank: 'D' },
    { min: 0, max: 499, rank: 'D-' },
  ];

  for (const { min, max, rank } of ranks) {
    if (elo >= min && elo <= max) {
      // Calculate progress within this rank tier
      const progress = ((elo - min) / (max - min)) * 100;
      return { rank, progress: Math.round(progress) };
    }
  }
  // Default to the lowest rank if not found
  return { rank: 'D-', progress: 0 };
};

export default getRankAndProgress;