export class AppError extends Error {
  constructor(message, statusCode = 500, code = 'INTERNAL_ERROR', details = null) {
    super(message);
    this.name = 'AppError';
    this.statusCode = statusCode;
    this.code = code;
    this.details = details;
    this.isOperational = true;
    Error.captureStackTrace(this, this.constructor);
  }

  static notFound(msg = 'Resource not found') { return new AppError(msg, 404, 'NOT_FOUND'); }
  static conflict(msg) { return new AppError(msg, 409, 'CONFLICT'); }
  static badRequest(msg) { return new AppError(msg, 400, 'BAD_REQUEST'); }
}

export const handleError = (error) => {
  if (error instanceof AppError) {
    return { success: false, error: { message: error.message, code: error.code, details: error.details } };
  }
  if (error.code === '23505') return { success: false, error: { message: 'Duplicate value', code: 'DUPLICATE_ERROR', details: error.detail } };
  if (error.code === '23503') return { success: false, error: { message: 'Referenced resource not found', code: 'FOREIGN_KEY_ERROR', details: error.detail } };
  console.error('Unhandled error:', error);
  return { success: false, error: { message: 'An unexpected error occurred', code: 'INTERNAL_ERROR' } };
};