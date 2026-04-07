import { describe, it, expect } from 'vitest';
import type { Task, CreateTaskRequest, UpdateTaskRequest, TaskStatus } from './task.model';

describe('Task model', () => {
  it('should allow a valid Task object', () => {
    const task: Task = {
      id: '550e8400-e29b-41d4-a716-446655440000',
      userId: '550e8400-e29b-41d4-a716-446655440001',
      title: 'Buy groceries',
      completed: false,
    };
    expect(task.id).toBe('550e8400-e29b-41d4-a716-446655440000');
    expect(task.userId).toBe('550e8400-e29b-41d4-a716-446655440001');
    expect(task.title).toBe('Buy groceries');
    expect(task.completed).toBe(false);
  });

  it('should allow Task with completed=true', () => {
    const task: Task = {
      id: 'abc',
      userId: 'def',
      title: 'Done task',
      completed: true,
    };
    expect(task.completed).toBe(true);
  });

  it('should allow a valid CreateTaskRequest', () => {
    const req: CreateTaskRequest = { title: 'New task' };
    expect(req.title).toBe('New task');
  });

  it('should allow a valid UpdateTaskRequest', () => {
    const req: UpdateTaskRequest = { title: 'Updated title' };
    expect(req.title).toBe('Updated title');
  });

  it('should allow pending TaskStatus', () => {
    const status: TaskStatus = 'pending';
    expect(status).toBe('pending');
  });

  it('should allow completed TaskStatus', () => {
    const status: TaskStatus = 'completed';
    expect(status).toBe('completed');
  });
});
