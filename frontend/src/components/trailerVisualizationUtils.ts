export function buildSlots(capacity: number) {
  const lowerCount = Math.max(1, Math.ceil(capacity / 2));
  const upperCount = Math.max(0, capacity - lowerCount);
  const lower = Array.from({ length: lowerCount }, (_, index) => ({
    position: index + 1,
    upperDeck: false,
  }));
  const upper = Array.from({ length: upperCount }, (_, index) => ({
    position: lowerCount + index + 1,
    upperDeck: true,
  }));
  return { lower, upper };
}
