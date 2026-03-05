import { clsx } from "clsx";
import { twMerge } from "tailwind-merge"

export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

/**
 * Safely extracts a string error message from an API error response.
 * Especially handles FastAPI/Pydantic validation error objects.
 */
export function getErrorMessage(error, defaultMessage = "An unexpected error occurred.") {
  if (!error) return defaultMessage;

  const detail = error.response?.data?.detail;

  if (!detail) return error.message || defaultMessage;

  if (typeof detail === 'string') return detail;

  if (Array.isArray(detail)) {
    // Handle Pydantic validation errors which come as an array of objects
    return detail.map(err => `${err.loc.join('.')}: ${err.msg}`).join(', ');
  }

  if (typeof detail === 'object') {
    // Handle other object-based error details
    return JSON.stringify(detail);
  }

  return defaultMessage;
}
