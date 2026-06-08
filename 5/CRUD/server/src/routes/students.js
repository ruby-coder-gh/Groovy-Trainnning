import express from 'express';
import { studentController } from '../controllers/studentController.js';
import { validateStudent, validateStudentUpdate, validateId } from '../middleware/validation.js';

const router = express.Router();

router.get('/stats', studentController.getStats);
router.get('/majors', studentController.getMajors);
router.get('/', studentController.getAll);
router.get('/:id', validateId, studentController.getById);
router.post('/', validateStudent, studentController.create);
router.put('/:id', validateId, validateStudentUpdate, studentController.update);
router.patch('/:id', validateId, validateStudentUpdate, studentController.update);
router.delete('/:id', validateId, studentController.delete);

export default router;