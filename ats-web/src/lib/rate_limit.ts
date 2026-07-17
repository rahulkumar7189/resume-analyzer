// src/lib/rate_limit.ts
type RateLimitInfo = {
  count: number;
  resetTime: number;
};

const rateLimitCache = new Map<string, RateLimitInfo>();

/**
 * Validates a rate limit for a given identifier (e.g., user ID or IP).
 * @param identifier The unique identifier for the client (e.g., email or session ID)
 * @param limit Maximum number of requests allowed
 * @param windowMs Time window in milliseconds (e.g., 60000 for 1 minute)
 * @returns { success: boolean, limit: number, remaining: number, reset: number }
 */
export function rateLimit(identifier: string, limit: number, windowMs: number) {
  const now = Date.now();
  const info = rateLimitCache.get(identifier);

  if (!info || now > info.resetTime) {
    // First request or window expired
    rateLimitCache.set(identifier, {
      count: 1,
      resetTime: now + windowMs,
    });
    return { success: true, limit, remaining: limit - 1, reset: now + windowMs };
  }

  if (info.count >= limit) {
    // Rate limit exceeded
    return { success: false, limit, remaining: 0, reset: info.resetTime };
  }

  // Increment count
  info.count += 1;
  return { success: true, limit, remaining: limit - info.count, reset: info.resetTime };
}
