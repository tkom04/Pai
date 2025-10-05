"use client"
import { useState, useEffect } from 'react'
import api from '@/lib/api'
import { handleApiError, showToast } from '@/lib/errorHandler'
import { Card } from './ui/Card'

interface Device {
  entity_id: string
  state: string
  attributes: {
    friendly_name?: string
    brightness?: number
    temperature?: number
    unit_of_measurement?: string
    device_class?: string
    icon?: string
  }
  last_changed: string
  last_updated: string
}

interface Service {
  domain: string
  service: string
  name?: string
  description?: string
  fields?: Record<string, any>
}

const HomeAssistantView = () => {
  const [devices, setDevices] = useState<Device[]>([])
  const [services, setServices] = useState<Service[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedRoom, setSelectedRoom] = useState<string>('all')
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    setLoading(true)
    try {
      const [devicesRes, servicesRes] = await Promise.all([
        api.get('/ha_entities'),
        api.get('/ha_recent_calls')
      ])
      setDevices(devicesRes.data.devices || [])
      setServices(servicesRes.data.services || [])
    } catch (error) {
      showToast(`Failed to fetch Home Assistant data: ${handleApiError(error)}`, 'error')
    } finally {
      setLoading(false)
    }
  }

  const toggleDevice = async (entityId: string) => {
    try {
      await api.post('/ha_service_call', { domain: 'homeassistant', service: 'toggle', entity_id: entityId })
      showToast('Device toggled successfully', 'success')
      fetchData()
    } catch (error) {
      showToast(`Failed to toggle device: ${handleApiError(error)}`, 'error')
    }
  }

  const callService = async (domain: string, service: string, data: any) => {
    try {
      await api.post('/ha_service_call', { domain, service, entity_id: data.entity_id })
      showToast('Service called successfully', 'success')
      fetchData()
    } catch (error) {
      showToast(`Failed to call service: ${handleApiError(error)}`, 'error')
    }
  }

  // Categorize devices by room
  const getRoomFromDevice = (device: Device): string => {
    const name = device.attributes.friendly_name || device.entity_id
    if (name.toLowerCase().includes('bedroom')) return 'bedroom'
    if (name.toLowerCase().includes('living')) return 'living room'
    if (name.toLowerCase().includes('kitchen')) return 'kitchen'
    if (name.toLowerCase().includes('bathroom')) return 'bathroom'
    if (name.toLowerCase().includes('office')) return 'office'
    if (name.toLowerCase().includes('garage')) return 'garage'
    if (name.toLowerCase().includes('outdoor') || name.toLowerCase().includes('outside')) return 'outdoor'
    return 'other'
  }

  // Get device icon
  const getDeviceIcon = (device: Device): string => {
    const entityType = device.entity_id.split('.')[0]
    const deviceClass = device.attributes.device_class

    if (device.attributes.icon) {
      const iconMap: { [key: string]: string } = {
        'mdi:lightbulb': '💡',
        'mdi:thermometer': '🌡️',
        'mdi:lock': '🔒',
        'mdi:camera': '📷',
        'mdi:motion-sensor': '🚶',
        'mdi:door': '🚪',
        'mdi:window': '🪟',
        'mdi:fan': '💨',
        'mdi:television': '📺',
        'mdi:speaker': '🔊',
        'mdi:power-plug': '🔌'
      }
      return iconMap[device.attributes.icon] || '🏠'
    }

    switch (entityType) {
      case 'light': return '💡'
      case 'switch': return '🔌'
      case 'climate': return '🌡️'
      case 'lock': return '🔒'
      case 'camera': return '📷'
      case 'media_player': return '📺'
      case 'sensor':
        if (deviceClass === 'temperature') return '🌡️'
        if (deviceClass === 'humidity') return '💧'
        if (deviceClass === 'motion') return '🚶'
        if (deviceClass === 'door') return '🚪'
        if (deviceClass === 'window') return '🪟'
        return '📊'
      case 'binary_sensor':
        if (deviceClass === 'motion') return '🚶'
        if (deviceClass === 'door') return '🚪'
        if (deviceClass === 'window') return '🪟'
        return '🔲'
      default: return '🏠'
    }
  }

  // Get device color based on state
  const getDeviceColor = (device: Device): string => {
    if (device.state === 'on' || device.state === 'home' || device.state === 'unlocked') {
      return 'bg-green-500'
    }
    if (device.state === 'off' || device.state === 'away' || device.state === 'locked') {
      return 'bg-gray-500'
    }
    if (device.state === 'unavailable' || device.state === 'unknown') {
      return 'bg-red-500'
    }
    return 'bg-blue-500'
  }

  // Filter devices by selected room
  const filteredDevices = selectedRoom === 'all'
    ? devices
    : devices.filter(device => getRoomFromDevice(device) === selectedRoom)

  // Get unique rooms
  const rooms = ['all', ...Array.from(new Set(devices.map(getRoomFromDevice)))]

  // Room icons
  const roomIcons: { [key: string]: string } = {
    'all': '🏠',
    'bedroom': '🛏️',
    'living room': '🛋️',
    'kitchen': '🍳',
    'bathroom': '🚿',
    'office': '💼',
    'garage': '🚗',
    'outdoor': '🌳',
    'other': '📦'
  }

  const DeviceCard = ({ device }: { device: Device }) => {
    const isToggleable = ['light', 'switch', 'media_player'].includes(device.entity_id.split('.')[0])
    const isOn = device.state === 'on'
    const value = device.attributes.brightness
      ? `${Math.round((device.attributes.brightness / 255) * 100)}%`
      : device.attributes.temperature
      ? `${device.attributes.temperature}${device.attributes.unit_of_measurement || '°'}`
      : device.state

    return (
      <div
        onClick={() => setSelectedDevice(device)}
        className="p-4 rounded-xl bg-white/5 hover:bg-white/10 transition-all cursor-pointer group"
      >
        <div className="flex items-start justify-between mb-3">
          <span className="text-2xl">{getDeviceIcon(device)}</span>
          <div className={`w-2 h-2 rounded-full ${getDeviceColor(device)}`}></div>
        </div>

        <h4 className="font-medium text-sm mb-1">
          {device.attributes.friendly_name || device.entity_id}
        </h4>
        <p className="text-xs text-white/50">{value}</p>

        {isToggleable && (
          <button
            onClick={(e) => {
              e.stopPropagation()
              toggleDevice(device.entity_id)
            }}
            className={`mt-3 w-full py-2 rounded-lg text-xs font-medium transition-all ${
              isOn
                ? 'bg-purple-600 hover:bg-purple-700 text-white'
                : 'bg-white/10 hover:bg-white/20 text-white/70'
            }`}
          >
            {isOn ? 'On' : 'Off'}
          </button>
        )}
      </div>
    )
  }

  return (
    <div className="p-6 h-full overflow-y-auto">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold mb-2">Smart Home</h1>
            <p className="text-white/50">Control your home devices</p>
          </div>
          <button
            onClick={fetchData}
            className="btn-primary mt-4 md:mt-0"
          >
            🔄 Refresh
          </button>
        </div>

        {/* Room Selector */}
        <div className="flex flex-wrap gap-3 mb-8">
          {rooms.map((room) => (
            <button
              key={room}
              onClick={() => setSelectedRoom(room)}
              className={`px-4 py-2 rounded-lg flex items-center space-x-2 transition-all ${
                selectedRoom === room
                  ? 'bg-purple-600 text-white'
                  : 'bg-white/5 text-white/70 hover:bg-white/10 hover:text-white'
              }`}
            >
              <span>{roomIcons[room]}</span>
              <span className="capitalize">{room}</span>
              {room !== 'all' && (
                <span className="text-xs">
                  ({devices.filter(d => getRoomFromDevice(d) === room).length})
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-white/50">Total Devices</p>
                <p className="text-2xl font-bold">{devices.length}</p>
              </div>
              <span className="text-2xl">🏠</span>
            </div>
          </Card>
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-white/50">Active</p>
                <p className="text-2xl font-bold">
                  {devices.filter(d => d.state === 'on').length}
                </p>
              </div>
              <span className="text-2xl">✅</span>
            </div>
          </Card>
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-white/50">Lights On</p>
                <p className="text-2xl font-bold">
                  {devices.filter(d => d.entity_id.startsWith('light.') && d.state === 'on').length}
                </p>
              </div>
              <span className="text-2xl">💡</span>
            </div>
          </Card>
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-white/50">Services</p>
                <p className="text-2xl font-bold">{services.length}</p>
              </div>
              <span className="text-2xl">⚙️</span>
            </div>
          </Card>
        </div>

        {/* Devices Grid */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">
            {selectedRoom === 'all' ? 'All Devices' : `${selectedRoom.charAt(0).toUpperCase() + selectedRoom.slice(1)} Devices`}
          </h3>

          {loading ? (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {[1, 2, 3, 4, 5, 6, 7, 8].map(i => (
                <div key={i} className="skeleton h-32"></div>
              ))}
            </div>
          ) : filteredDevices.length > 0 ? (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {filteredDevices.map(device => (
                <DeviceCard key={device.entity_id} device={device} />
              ))}
            </div>
          ) : (
            <p className="text-white/50 text-center py-12">No devices found</p>
          )}
        </Card>
      </div>

      {/* Device Details Modal */}
      {selectedDevice && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <Card className="w-full max-w-md p-6">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center space-x-3">
                <span className="text-2xl">{getDeviceIcon(selectedDevice)}</span>
                <h2 className="text-xl font-bold">
                  {selectedDevice.attributes.friendly_name || selectedDevice.entity_id}
                </h2>
              </div>
              <button
                onClick={() => setSelectedDevice(null)}
                className="text-white/50 hover:text-white"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-white/50 mb-1">State</p>
                  <div className="flex items-center space-x-2">
                    <div className={`w-3 h-3 rounded-full ${getDeviceColor(selectedDevice)}`}></div>
                    <span className="capitalize">{selectedDevice.state}</span>
                  </div>
                </div>
                <div>
                  <p className="text-sm text-white/50 mb-1">Entity ID</p>
                  <p className="text-sm font-mono">{selectedDevice.entity_id}</p>
                </div>
              </div>

              {selectedDevice.attributes.brightness && (
                <div>
                  <p className="text-sm text-white/50 mb-1">Brightness</p>
                  <p>{Math.round((selectedDevice.attributes.brightness / 255) * 100)}%</p>
                </div>
              )}

              {selectedDevice.attributes.temperature && (
                <div>
                  <p className="text-sm text-white/50 mb-1">Temperature</p>
                  <p>{selectedDevice.attributes.temperature}{selectedDevice.attributes.unit_of_measurement || '°'}</p>
                </div>
              )}

              <div>
                <p className="text-sm text-white/50 mb-1">Last Updated</p>
                <p className="text-sm">
                  {new Date(selectedDevice.last_updated).toLocaleString()}
                </p>
              </div>
            </div>

            <div className="flex justify-end space-x-3 mt-6">
              {['light', 'switch', 'media_player'].includes(selectedDevice.entity_id.split('.')[0]) && (
                <button
                  onClick={() => {
                    toggleDevice(selectedDevice.entity_id)
                    setSelectedDevice(null)
                  }}
                  className="btn-secondary"
                >
                  Toggle
                </button>
              )}
              <button
                onClick={() => setSelectedDevice(null)}
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

export default HomeAssistantView