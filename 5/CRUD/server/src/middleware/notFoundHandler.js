import { AppError } from '../utils/AppError.js';
export const notFoundHandler = (req, res, next) => { throw new AppError(`Route ${req.method} ${req.path} not found`, 404, 'ROUTE_NOT_FOUND'); };
export default notFoundHandler;