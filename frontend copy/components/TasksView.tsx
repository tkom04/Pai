"use client"
import { useState, useEffect } from 'react'
import api from '@/lib/api'
import { handleApiError, showToast } from '@/lib/errorHandler'
import { Card } from './ui/Card'

interface Task {
  id: string
  title: string
  description?: string
  status: 'todo' | 'in_progress' | 'done'
  priority: 'low' | 'medium' | 'high' | 'urgent'
  due_date?: string
  tags?: string[]
  created_at: string
  updated_at: string
}

const TasksView = () => {
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [selectedTask, setSelectedTask] = useState<Task | null>(null)
  const [filter, setFilter] = useState<'all' | 'todo' | 'in_progress' | 'done'>('all')

  const [newTask, setNewTask] = useState({
    title: '',
    description: '',
    status: 'todo' as const,
    priority: 'medium' as 'low' | 'medium' | 'high' | 'urgent',
    due_date: '',
    tags: ''
  })

  useEffect(() => {
    fetchTasks()
  }, [])

  const fetchTasks = async () => {
    setLoading(true)
    try {
      const response = await api.get('/tasks')
      setTasks(response.data.tasks || [])
    } catch (error) {
      showToast(`Failed to fetch tasks: ${handleApiError(error)}`, 'error')
      setTasks([])
    } finally {
      setLoading(false)
    }
  }

  const createTask = async () => {
    if (!newTask.title) {
      showToast('Please enter a task title', 'error')
      return
    }

    try {
      const taskData = {
        ...newTask,
        tags: newTask.tags ? newTask.tags.split(',').map(tag => tag.trim()) : []
      }

      await api.post('/tasks', taskData)
      showToast('Task created successfully', 'success')
      setShowCreateModal(false)
      setNewTask({
        title: '',
        description: '',
        status: 'todo',
        priority: 'medium',
        due_date: '',
        tags: ''
      })
      fetchTasks()
    } catch (error) {
      showToast(`Failed to create task: ${handleApiError(error)}`, 'error')
    }
  }

  const updateTaskStatus = async (taskId: string, newStatus: Task['status']) => {
    try {
      await api.patch(`/tasks/${taskId}`, { status: newStatus })
      showToast('Task updated successfully', 'success')
      fetchTasks()
    } catch (error) {
      showToast(`Failed to update task: ${handleApiError(error)}`, 'error')
    }
  }

  const deleteTask = async (taskId: string) => {
    try {
      await api.delete(`/tasks/${taskId}`)
      showToast('Task deleted successfully', 'success')
      setSelectedTask(null)
      fetchTasks()
    } catch (error) {
      showToast(`Failed to delete task: ${handleApiError(error)}`, 'error')
    }
  }

  const getPriorityColor = (priority: Task['priority']) => {
    switch (priority) {
      case 'urgent': return 'bg-red-500'
      case 'high': return 'bg-orange-500'
      case 'medium': return 'bg-yellow-500'
      case 'low': return 'bg-green-500'
      default: return 'bg-gray-500'
    }
  }

  const getStatusIcon = (status: Task['status']) => {
    switch (status) {
      case 'todo': return '⭕'
      case 'in_progress': return '🔄'
      case 'done': return '✅'
      default: return '📋'
    }
  }

  const filteredTasks = tasks.filter(task =>
    filter === 'all' || task.status === filter
  )

  const tasksByStatus = {
    todo: filteredTasks.filter(task => task.status === 'todo'),
    in_progress: filteredTasks.filter(task => task.status === 'in_progress'),
    done: filteredTasks.filter(task => task.status === 'done')
  }

  const TaskCard = ({ task }: { task: Task }) => (
    <div
      onClick={() => setSelectedTask(task)}
      className="p-4 rounded-xl bg-white/5 hover:bg-white/10 transition-all cursor-pointer group"
    >
      <div className="flex items-start justify-between mb-2">
        <span className="text-lg">{getStatusIcon(task.status)}</span>
        <div className={`w-2 h-2 rounded-full ${getPriorityColor(task.priority)}`}></div>
      </div>

      <h4 className="font-medium mb-1">{task.title}</h4>
      {task.description && (
        <p className="text-sm text-white/50 line-clamp-2">{task.description}</p>
      )}

      <div className="flex items-center justify-between mt-3">
        {task.due_date && (
          <p className="text-xs text-white/50">
            Due: {new Date(task.due_date).toLocaleDateString()}
          </p>
        )}
        {task.tags && task.tags.length > 0 && (
          <div className="flex gap-1">
            {task.tags.slice(0, 2).map((tag, i) => (
              <span key={i} className="text-xs bg-white/10 px-2 py-1 rounded-full">
                {tag}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  )

  return (
    <div className="p-6 h-full overflow-y-auto">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold mb-2">Tasks</h1>
            <p className="text-white/50">Manage your tasks and to-dos</p>
          </div>
          <div className="flex items-center space-x-3 mt-4 md:mt-0">
            {/* Filter */}
            <div className="flex bg-white/5 rounded-lg p-1">
              {(['all', 'todo', 'in_progress', 'done'] as const).map((f) => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                    filter === f
                      ? 'bg-purple-600 text-white'
                      : 'text-white/70 hover:text-white'
                  }`}
                >
                  {f === 'all' ? 'All' : f.replace('_', ' ').charAt(0).toUpperCase() + f.slice(1).replace('_', ' ')}
                </button>
              ))}
            </div>
            <button
              onClick={() => setShowCreateModal(true)}
              className="btn-primary"
            >
              + New Task
            </button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-white/50">Total Tasks</p>
                <p className="text-2xl font-bold">{tasks.length}</p>
              </div>
              <span className="text-2xl">📊</span>
            </div>
          </Card>
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-white/50">To Do</p>
                <p className="text-2xl font-bold">{tasksByStatus.todo.length}</p>
              </div>
              <span className="text-2xl">⭕</span>
            </div>
          </Card>
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-white/50">In Progress</p>
                <p className="text-2xl font-bold">{tasksByStatus.in_progress.length}</p>
              </div>
              <span className="text-2xl">🔄</span>
            </div>
          </Card>
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-white/50">Completed</p>
                <p className="text-2xl font-bold">{tasksByStatus.done.length}</p>
              </div>
              <span className="text-2xl">✅</span>
            </div>
          </Card>
        </div>

        {/* Kanban Board */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* To Do Column */}
          <Card className="p-4">
            <h3 className="font-semibold mb-4 flex items-center justify-between">
              <span>To Do</span>
              <span className="text-sm text-white/50">{tasksByStatus.todo.length}</span>
            </h3>
            <div className="space-y-3">
              {loading ? (
                [1, 2].map(i => (
                  <div key={i} className="skeleton h-24"></div>
                ))
              ) : tasksByStatus.todo.length > 0 ? (
                tasksByStatus.todo.map(task => (
                  <TaskCard key={task.id} task={task} />
                ))
              ) : (
                <p className="text-white/50 text-center py-8">No tasks</p>
              )}
            </div>
          </Card>

          {/* In Progress Column */}
          <Card className="p-4">
            <h3 className="font-semibold mb-4 flex items-center justify-between">
              <span>In Progress</span>
              <span className="text-sm text-white/50">{tasksByStatus.in_progress.length}</span>
            </h3>
            <div className="space-y-3">
              {loading ? (
                [1, 2].map(i => (
                  <div key={i} className="skeleton h-24"></div>
                ))
              ) : tasksByStatus.in_progress.length > 0 ? (
                tasksByStatus.in_progress.map(task => (
                  <TaskCard key={task.id} task={task} />
                ))
              ) : (
                <p className="text-white/50 text-center py-8">No tasks</p>
              )}
            </div>
          </Card>

          {/* Done Column */}
          <Card className="p-4">
            <h3 className="font-semibold mb-4 flex items-center justify-between">
              <span>Done</span>
              <span className="text-sm text-white/50">{tasksByStatus.done.length}</span>
            </h3>
            <div className="space-y-3">
              {loading ? (
                [1, 2].map(i => (
                  <div key={i} className="skeleton h-24"></div>
                ))
              ) : tasksByStatus.done.length > 0 ? (
                tasksByStatus.done.map(task => (
                  <TaskCard key={task.id} task={task} />
                ))
              ) : (
                <p className="text-white/50 text-center py-8">No completed tasks</p>
              )}
            </div>
          </Card>
        </div>
      </div>

      {/* Create Task Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-md p-6 max-h-[90vh] overflow-y-auto">
            <h2 className="text-2xl font-bold mb-6">Create New Task</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Title *</label>
                <input
                  type="text"
                  value={newTask.title}
                  onChange={(e) => setNewTask({ ...newTask, title: e.target.value })}
                  className="input"
                  placeholder="Task title"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Description</label>
                <textarea
                  value={newTask.description}
                  onChange={(e) => setNewTask({ ...newTask, description: e.target.value })}
                  className="input min-h-[100px]"
                  placeholder="Task description"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Priority</label>
                  <select
                    value={newTask.priority}
                    onChange={(e) => setNewTask({ ...newTask, priority: e.target.value as 'low' | 'medium' | 'high' | 'urgent' })}
                    className="input"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="urgent">Urgent</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Due Date</label>
                  <input
                    type="date"
                    value={newTask.due_date}
                    onChange={(e) => setNewTask({ ...newTask, due_date: e.target.value })}
                    className="input"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Tags</label>
                <input
                  type="text"
                  value={newTask.tags}
                  onChange={(e) => setNewTask({ ...newTask, tags: e.target.value })}
                  className="input"
                  placeholder="Comma separated tags"
                />
              </div>
            </div>

            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowCreateModal(false)}
                className="btn-ghost"
              >
                Cancel
              </button>
              <button
                onClick={createTask}
                className="btn-primary"
              >
                Create Task
              </button>
            </div>
          </Card>
        </div>
      )}

      {/* Task Details Modal */}
      {selectedTask && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-md p-6">
            <div className="flex items-start justify-between mb-4">
              <h2 className="text-xl font-bold">{selectedTask.title}</h2>
              <button
                onClick={() => setSelectedTask(null)}
                className="text-white/50 hover:text-white"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              {selectedTask.description && (
                <div>
                  <p className="text-sm text-white/50 mb-1">Description</p>
                  <p className="text-white/80">{selectedTask.description}</p>
                </div>
              )}

              <div className="flex items-center space-x-4">
                <div>
                  <p className="text-sm text-white/50 mb-1">Status</p>
                  <select
                    value={selectedTask.status}
                    onChange={(e) => updateTaskStatus(selectedTask.id, e.target.value as Task['status'])}
                    className="input"
                  >
                    <option value="todo">To Do</option>
                    <option value="in_progress">In Progress</option>
                    <option value="done">Done</option>
                  </select>
                </div>

                <div>
                  <p className="text-sm text-white/50 mb-1">Priority</p>
                  <div className="flex items-center space-x-2">
                    <div className={`w-3 h-3 rounded-full ${getPriorityColor(selectedTask.priority)}`}></div>
                    <span className="capitalize">{selectedTask.priority}</span>
                  </div>
                </div>
              </div>

              {selectedTask.due_date && (
                <div>
                  <p className="text-sm text-white/50 mb-1">Due Date</p>
                  <p>{new Date(selectedTask.due_date).toLocaleDateString()}</p>
                </div>
              )}

              {selectedTask.tags && selectedTask.tags.length > 0 && (
                <div>
                  <p className="text-sm text-white/50 mb-1">Tags</p>
                  <div className="flex flex-wrap gap-2">
                    {selectedTask.tags.map((tag, i) => (
                      <span key={i} className="text-sm bg-white/10 px-3 py-1 rounded-full">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => deleteTask(selectedTask.id)}
                className="btn-ghost text-red-400 hover:text-red-300"
              >
                Delete
              </button>
              <button
                onClick={() => setSelectedTask(null)}
                className="btn-primary"
              >
                Close
              </button>
            </div>
          </Card>
        </div>
      )}
    </div>
  )
}

export default TasksView