import { gsap } from 'gsap';

/**
 * GSAP Animation Utilities for ScrimGG
 * FACEIT-inspired competitive animations
 */

// Default easing configurations
export const ease = {
  smooth: 'power2.out',
  snappy: 'power3.out',
  aggressive: 'power4.out',
  elastic: 'elastic.out(1, 0.5)',
  bounce: 'back.out(1.7)',
};

// Page fade in animation
export const fadeIn = (element, options = {}) => {
  const {
    duration = 0.6,
    delay = 0,
    y = 20,
    ease: customEase = ease.smooth,
  } = options;

  return gsap.from(element, {
    opacity: 0,
    y,
    duration,
    delay,
    ease: customEase,
  });
};

// Stagger animation for lists/grids
export const staggerIn = (elements, options = {}) => {
  const {
    duration = 0.5,
    stagger = 0.1,
    delay = 0,
    y = 30,
    ease: customEase = ease.snappy,
  } = options;

  return gsap.from(elements, {
    opacity: 0,
    y,
    duration,
    stagger,
    delay,
    ease: customEase,
  });
};

// Scale in animation (for cards, buttons)
export const scaleIn = (element, options = {}) => {
  const {
    duration = 0.4,
    delay = 0,
    scale = 0.9,
    ease: customEase = ease.bounce,
  } = options;

  return gsap.from(element, {
    opacity: 0,
    scale,
    duration,
    delay,
    ease: customEase,
  });
};

// Slide in from direction
export const slideIn = (element, options = {}) => {
  const {
    duration = 0.6,
    delay = 0,
    direction = 'left', // left, right, top, bottom
    distance = 100,
    ease: customEase = ease.aggressive,
  } = options;

  const props = {
    opacity: 0,
    duration,
    delay,
    ease: customEase,
  };

  switch (direction) {
    case 'left':
      props.x = -distance;
      break;
    case 'right':
      props.x = distance;
      break;
    case 'top':
      props.y = -distance;
      break;
    case 'bottom':
      props.y = distance;
      break;
    default:
      props.x = -distance;
  }

  return gsap.from(element, props);
};

// Competitive reveal animation (like FACEIT match cards)
export const competitiveReveal = (element, options = {}) => {
  const {
    duration = 0.8,
    delay = 0,
  } = options;

  const tl = gsap.timeline({ delay });

  tl.from(element, {
    opacity: 0,
    scale: 0.95,
    duration: duration * 0.6,
    ease: ease.smooth,
  })
    .from(element, {
      y: 20,
      duration: duration * 0.4,
      ease: ease.aggressive,
    }, `-=${duration * 0.3}`);

  return tl;
};

// Hover scale effect
export const hoverScale = (element, options = {}) => {
  const {
    scale = 1.05,
    duration = 0.3,
  } = options;

  element.addEventListener('mouseenter', () => {
    gsap.to(element, {
      scale,
      duration,
      ease: ease.snappy,
    });
  });

  element.addEventListener('mouseleave', () => {
    gsap.to(element, {
      scale: 1,
      duration,
      ease: ease.snappy,
    });
  });
};

// Number counter animation
export const counterAnimation = (element, options = {}) => {
  const {
    from = 0,
    to = 100,
    duration = 1.5,
    delay = 0,
  } = options;

  const obj = { value: from };

  return gsap.to(obj, {
    value: to,
    duration,
    delay,
    ease: 'power1.out',
    onUpdate: () => {
      element.textContent = Math.floor(obj.value);
    },
  });
};

// Page transition out
export const pageOut = (element, options = {}) => {
  const {
    duration = 0.4,
    y = -30,
  } = options;

  return gsap.to(element, {
    opacity: 0,
    y,
    duration,
    ease: ease.snappy,
  });
};

// Glow pulse effect
export const glowPulse = (element, options = {}) => {
  const {
    duration = 2,
    color = '#ff4655',
    intensity = 20,
  } = options;

  return gsap.to(element, {
    boxShadow: `0 0 ${intensity}px ${color}`,
    duration,
    repeat: -1,
    yoyo: true,
    ease: 'sine.inOut',
  });
};

// Text reveal animation
export const textReveal = (element, options = {}) => {
  const {
    duration = 0.8,
    delay = 0,
    stagger = 0.03,
  } = options;

  const chars = element.textContent.split('');
  element.textContent = '';

  chars.forEach(char => {
    const span = document.createElement('span');
    span.textContent = char === ' ' ? '\u00A0' : char;
    span.style.display = 'inline-block';
    element.appendChild(span);
  });

  return gsap.from(element.children, {
    opacity: 0,
    y: 20,
    duration,
    delay,
    stagger,
    ease: ease.smooth,
  });
};

export default {
  fadeIn,
  staggerIn,
  scaleIn,
  slideIn,
  competitiveReveal,
  hoverScale,
  counterAnimation,
  pageOut,
  glowPulse,
  textReveal,
  ease,
};
