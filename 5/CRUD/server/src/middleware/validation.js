import Joi from 'joi';
import { AppError } from '../utils/AppError.js';

const studentSchema = Joi.object({
  firstName: Joi.string().min(1).max(100).required().trim(),
  lastName: Joi.string().min(1).max(100).required().trim(),
  email: Joi.string().email().max(255).required().trim().lowercase(),
  phone: Joi.string().max(20).allow('', null).pattern(/^[\d\s\-\+\(\)]{7,20}$/).optional(),
  dateOfBirth: Joi.date().max('now').optional(),
  enrollmentDate: Joi.date().optional(),
  major: Joi.string().max(100).allow('', null).optional().trim(),
  gpa: Joi.number().min(0).max(4.0).precision(2).optional(),
  status: Joi.string().valid('active', 'inactive', 'graduated', 'suspended').optional()
});

const studentUpdateSchema = studentSchema.fork(['firstName', 'lastName', 'email'], (s) => s.optional());
const idSchema = Joi.string().uuid().required();

export const validate = (schema, prop = 'body') => (req, res, next) => {
  const { error, value } = schema.validate(req[prop], { abortEarly: false, stripUnknown: true });
  if (error) {
    const details = error.details.map(d => ({ field: d.path.join('.'), message: d.message }));
    throw new AppError('Validation failed', 422, 'VALIDATION_ERROR', details);
  }
  req[prop] = value;
  next();
};

export const validateStudent = validate(studentSchema);
export const validateStudentUpdate = validate(studentUpdateSchema);

// ID param validation — validate req.params.id, not the whole params object
export const validateId = (req, res, next) => {
  const { error, value } = idSchema.validate(req.params.id);
  if (error) {
    throw new AppError('Invalid student ID format', 422, 'VALIDATION_ERROR', [{ field: 'id', message: 'Invalid UUID format' }]);
  }
  req.params.id = value;
  next();
};