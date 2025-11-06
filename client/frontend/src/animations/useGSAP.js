import { useEffect, useRef } from 'react';
import { gsap } from 'gsap';

/**
 * Custom hook for GSAP animations
 * Provides automatic cleanup and timeline management
 */

export const useGSAP = (animationCallback, dependencies = []) => {
  const timelineRef = useRef(null);

  useEffect(() => {
    // Create a new timeline
    const ctx = gsap.context(() => {
      timelineRef.current = animationCallback();
    });

    // Cleanup on unmount
    return () => {
      ctx.revert();
    };
  }, dependencies);

  return timelineRef;
};

/**
 * Hook for page enter animations
 */
export const usePageEnter = (containerRef, animationCallback, dependencies = []) => {
  useEffect(() => {
    if (!containerRef.current) return;

    const ctx = gsap.context(() => {
      animationCallback();
    }, containerRef);

    return () => ctx.revert();
  }, [containerRef, ...dependencies]);
};

/**
 * Hook for staggered children animations
 */
export const useStagger = (containerRef, selector, options = {}) => {
  useEffect(() => {
    if (!containerRef.current) return;

    const {
      duration = 0.6,
      stagger = 0.1,
      delay = 0,
      y = 30,
      ease = 'power2.out',
    } = options;

    const ctx = gsap.context(() => {
      gsap.from(selector, {
        opacity: 0,
        y,
        duration,
        stagger,
        delay,
        ease,
      });
    }, containerRef);

    return () => ctx.revert();
  }, [containerRef, selector]);
};

/**
 * Hook for hover animations
 */
export const useHoverAnimation = (elementRef, options = {}) => {
  useEffect(() => {
    if (!elementRef.current) return;

    const {
      scale = 1.05,
      duration = 0.3,
      ease = 'power2.out',
    } = options;

    const element = elementRef.current;

    const handleMouseEnter = () => {
      gsap.to(element, {
        scale,
        duration,
        ease,
      });
    };

    const handleMouseLeave = () => {
      gsap.to(element, {
        scale: 1,
        duration,
        ease,
      });
    };

    element.addEventListener('mouseenter', handleMouseEnter);
    element.addEventListener('mouseleave', handleMouseLeave);

    return () => {
      element.removeEventListener('mouseenter', handleMouseEnter);
      element.removeEventListener('mouseleave', handleMouseLeave);
    };
  }, [elementRef]);
};

export default {
  useGSAP,
  usePageEnter,
  useStagger,
  useHoverAnimation,
};
