export interface Zone {
  id:       string
  count:    number
  density:  number
  avgSpeed: number
  status:   'normal' | 'attention' | 'critical'
}

export interface Site {
  id:         string
  name:       string
  address:    string
  lat:        number
  lng:        number
  capacity:   number
  zones:      Record<string, Zone>
  inCount:    number
  outCount:   number
  totalPersons: number
  status:     'normal' | 'attention' | 'critical' | 'offline'
  lastUpdate: string
}

export interface Alert {
  id:          string
  level:       'info' | 'warning' | 'critical'
  siteId:      string
  siteName:    string
  zone:        string
  anomalyType: string
  message:     string
  timestamp:   string
  confidence:  number
  duration?:   number
  resolved:    boolean
  frameUrl?:   string
}

export interface Prediction {
  zone:     string
  h5:       number
  h10:      number
  h15:      number
  confidence: number
  trend:    'up' | 'down' | 'stable'
}

export interface SiteUpdate {
  timestamp: string
  siteId:    string
  zones:     Record<string, { count: number; density: number; avgSpeed: number }>
}

export interface AlertEvent {
  id:          string
  level:       'info' | 'warning' | 'critical'
  siteId:      string
  zone:        string
  anomalyType: string
  message:     string
  timestamp:   string
  confidence:  number
}
