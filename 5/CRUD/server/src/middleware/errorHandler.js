import { handleError } from '../utils/AppError.js';
export const errorHandler = (err, req, res, next) => {
  const statusCode = err.statusCode || 500;
  console.error(`[${new Date().toISOString()}] ${req.method} ${req.path} - ${statusCode}`, { error: err.message, code: err.code });
  res.status(statusCode).json(handleError(err));
};
export default errorHandler;