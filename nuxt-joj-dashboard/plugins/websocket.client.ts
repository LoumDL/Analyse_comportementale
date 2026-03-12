export default defineNuxtPlugin(() => {
  const { connect } = useWebSocket()
  connect()
})
