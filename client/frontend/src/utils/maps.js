const MAP_IMAGE_BY_SLUG = {
    bind: '/maps/bind.jpg',
    haven: '/maps/haven.jpg',
    split: '/maps/split.jpg',
    ascent: '/maps/ascent.jpg',
    icebox: '/maps/icebox.jpg',
    breeze: '/maps/breeze.jpg',
    fracture: '/maps/fracture.jpg',
    pearl: '/maps/pearl.jpg',
    lotus: '/maps/lotus.jpg',
    sunset: '/maps/sunset.jpg',
  };
  
  export function mapSlug(name) {
    return String(name || '')
      .toLowerCase()
      .replace(/\s+/g, '')         // remove spaces
      .replace(/[^a-z0-9]/g, '');  // strip non-alphanumerics
  }
  
  export function mapImageUrl(name, overrideUrl) {
    if (overrideUrl) return overrideUrl;             // allow server-provided URL
    const slug = mapSlug(name);
    return MAP_IMAGE_BY_SLUG[slug] || '/maps/default.jpg';
  }