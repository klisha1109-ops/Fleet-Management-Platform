import { useContext, useEffect, useMemo, useState } from "react";
import { Navigate } from "react-router-dom";
import { CircleMarker, MapContainer, Polyline, TileLayer, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import MainLayout from "../layouts/MainLayout";
import EmptyState from "../components/EmptyState";
import LoadingCard from "../components/LoadingCard";
import PageHeader from "../components/PageHeader";
import StatsCard from "../components/StatsCard";
import StatusBadge from "../components/StatusBadge";
import { AnalyticsBarChart, AnalyticsDonutChart } from "../components/AnalyticsCharts";
import api from "../services/api";
import { AuthContext } from "../context/auth-context";
import "./Analytics.css";
import "./LogisticsAnalytics.css";

const hours = (seconds) => seconds == null ? "Not calculated" : `${(Number(seconds) / 3600).toFixed(1)} h`;
const kilometres = (meters) => meters == null ? "Not calculated" : `${(Number(meters) / 1000).toFixed(1)} km`;

function RouteMapBounds({ geometry }) {
  const map = useMap();
  useEffect(() => {
    const positions = geometry.map(([longitude, latitude]) => [latitude, longitude]);
    if (positions.length > 1) map.fitBounds(positions, { padding: [24, 24] });
  }, [geometry, map]);
  return null;
}

function LogisticsAnalytics({ embedded = false }) {
  const { user } = useContext(AuthContext);
  const [data, setData] = useState(null); const [error, setError] = useState(""); const [loading, setLoading] = useState(true); const [selectedRouteTripId, setSelectedRouteTripId] = useState("");
  const allowed = ["Admin", "FleetManager", "Dispatcher"].includes(user?.role);
  const inLayout = (content) => embedded ? content : <MainLayout>{content}</MainLayout>;
  const load = async () => { setLoading(true); setError(""); try { const [shipmentResponse, tripResponse, deliveryResponse] = await Promise.all([api.get("/shipments/"), api.get("/trips/"), api.get("/analytics/delivery-performance")]); const activeTrips = tripResponse.data.filter((trip) => trip.status === "Active"); const routeResults = await Promise.allSettled(activeTrips.map((trip) => api.get(`/trips/${trip.trip_id}/route`))); const routes = routeResults.filter((result) => result.status === "fulfilled").map((result) => result.value.data); setData({ shipments: shipmentResponse.data, trips: tripResponse.data, delivery: deliveryResponse.data, routes }); setSelectedRouteTripId((current) => routes.some((route) => route.trip_id === current) ? current : routes[0]?.trip_id || ""); } catch (requestError) { setError(requestError.response?.data?.detail || "Unable to load logistics analytics."); } finally { setLoading(false); } };
  useEffect(() => { if (!allowed) return undefined; const timer = window.setTimeout(() => { void load(); }, 0); return () => window.clearTimeout(timer); }, [allowed]);
  const selectedRoute = useMemo(() => data?.routes.find((route) => route.trip_id === selectedRouteTripId) || null, [data?.routes, selectedRouteTripId]);
  const selectedTrip = useMemo(() => data?.trips.find((trip) => trip.trip_id === selectedRoute?.trip_id) || null, [data?.trips, selectedRoute]);
  if (!allowed && user) return <Navigate to="/dashboard" replace />;
  if (loading) return inLayout(<LoadingCard message="Loading logistics analytics..." />);
  if (error) return inLayout(<>{!embedded && <PageHeader eyebrow="Analytics" title="Logistics Analytics" description="Delivery performance and route visibility." />}<div className="analytics-error">{error}<button onClick={() => void load()}>Try again</button></div></>);
  const statusCounts = data.shipments.reduce((counts, shipment) => ({ ...counts, [shipment.status]: (counts[shipment.status] || 0) + 1 }), {});
  const active = (statusCounts.Created || 0) + (statusCounts.Assigned || 0) + (statusCounts["In Transit"] || 0) + (statusCounts.Delayed || 0);
  const calculatedTrips = data.trips.filter((trip) => trip.planned_distance != null || trip.estimated_duration != null);
  const averageDistance = calculatedTrips.length ? calculatedTrips.reduce((sum, trip) => sum + Number(trip.planned_distance || 0), 0) / calculatedTrips.length : null;
  const averageDuration = calculatedTrips.length ? calculatedTrips.reduce((sum, trip) => sum + Number(trip.estimated_duration || 0), 0) / calculatedTrips.length : null;
  const remainingDistance = data.routes.reduce((sum, route) => sum + Number(route.remaining_distance || 0), 0); const remainingDuration = data.routes.reduce((sum, route) => sum + Number(route.remaining_duration || 0), 0);
  const shipmentById = new Map(data.shipments.map((item) => [item.shipment_id, item])); const groups = {};
  data.trips.filter((trip) => trip.status === "Completed" && trip.ended_at).forEach((trip) => { const shipment = shipmentById.get(trip.shipment_id); if (!shipment?.expected_delivery_at) return; const label = new Date(trip.ended_at).toLocaleDateString(); const group = groups[label] || { label, onTime: 0, total: 0 }; group.total += 1; if (new Date(trip.ended_at) <= new Date(shipment.expected_delivery_at)) group.onTime += 1; groups[label] = group; });
  const onTimeTrend = Object.values(groups).sort((first, second) => new Date(first.label) - new Date(second.label)).map((item) => ({ label: item.label, value: Math.round((item.onTime / item.total) * 100) }));
  const mapPositions = selectedRoute?.geometry?.map(([longitude, latitude]) => [latitude, longitude]) || [];
  return inLayout(<>{!embedded && <PageHeader eyebrow="Analytics" title="Logistics Analytics" description="Delivery health, route performance, and live-route visibility." />}<div className="analytics-refresh"><span>Route maps use saved OSRM geometry. Vehicle movement requires fresh authorised GPS data.</span><button className="primary-button" onClick={() => void load()}>Refresh data</button></div><section className="analytics-kpis"><StatsCard label="Active Shipments" value={active} detail="Created to delayed" icon="▣" /><StatsCard label="Completed" value={statusCounts.Delivered || 0} detail="Delivered shipments" icon="✓" tone="green" /><StatsCard label="Delayed" value={statusCounts.Delayed || 0} detail="Needs attention" icon="!" tone="red" /><StatsCard label="In Transit" value={statusCounts["In Transit"] || 0} detail="Currently moving" icon="⌁" tone="purple" /><StatsCard label="On-time Rate" value={`${data.delivery.on_time_rate || 0}%`} detail={`${data.delivery.on_time_deliveries || 0} verified on time`} icon="◔" tone="green" /></section><section className="analytics-grid two"><article className="analytics-panel"><div className="analytics-panel-heading"><div><p>Delivery composition</p><h2>Shipment status breakdown</h2></div></div><AnalyticsDonutChart data={Object.entries(statusCounts).map(([label, value]) => ({ label, value }))} /></article><article className="analytics-panel"><div className="analytics-panel-heading"><div><p>On-time delivery</p><h2>Verified on-time percentage</h2></div></div><AnalyticsBarChart data={onTimeTrend} dataKey="value" name="On-time rate (%)" /></article></section><section className="analytics-grid two"><article className="analytics-panel"><div className="analytics-panel-heading"><div><p>OSRM routes</p><h2>Route performance</h2></div></div><div className="analytics-summary-list"><div><span>Average calculated distance</span><b>{kilometres(averageDistance)}</b></div><div><span>Average calculated duration</span><b>{hours(averageDuration)}</b></div><div><span>Active remaining distance</span><b>{data.routes.length ? kilometres(remainingDistance) : "No route data"}</b></div><div><span>Active remaining duration</span><b>{data.routes.length ? hours(remainingDuration) : "No route data"}</b></div></div></article><article className="analytics-panel"><div className="analytics-panel-heading"><div><p>OSRM route</p><h2>Active route map</h2></div>{selectedTrip && <StatusBadge status={selectedTrip.status} />}</div>{selectedRoute && mapPositions.length > 1 ? <><>{data.routes.length > 1 && <label className="analytics-route-select"><span>Active trip</span><select value={selectedRouteTripId} onChange={(event) => setSelectedRouteTripId(event.target.value)}>{data.routes.map((route) => { const trip = data.trips.find((item) => item.trip_id === route.trip_id); return <option key={route.trip_id} value={route.trip_id}>{trip ? `${trip.source} to ${trip.destination}` : route.trip_id}</option>; })}</select></label>}</><div className="analytics-route-map" aria-label="Active trip route map"><MapContainer center={mapPositions[0]} zoom={7} scrollWheelZoom><TileLayer attribution="&copy; OpenStreetMap contributors" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" /><Polyline positions={mapPositions} pathOptions={{ color: "#7254d8", weight: 5 }} /><CircleMarker center={mapPositions[0]} radius={7} pathOptions={{ color: "#16774c", fillColor: "#32b979", fillOpacity: 1 }} /><CircleMarker center={mapPositions[mapPositions.length - 1]} radius={7} pathOptions={{ color: "#b42b4a", fillColor: "#e45170", fillOpacity: 1 }} /><RouteMapBounds geometry={selectedRoute.geometry} /></MapContainer></div><p className="analytics-muted">Green marks the route start; red marks the destination. No vehicle movement is shown without fresh GPS telemetry.</p></> : <div className="analytics-no-data"><strong>No active calculated route</strong><p>Schedule, calculate, and start a trip to display its OSRM route here.</p></div>}</article></section><section className="analytics-panel"><div className="analytics-panel-heading"><div><p>Route directory</p><h2>Calculated trips</h2></div></div>{calculatedTrips.length ? <div className="analytics-table-wrap"><table><thead><tr><th>Route</th><th>Type</th><th>Distance</th><th>Duration</th><th>ETA</th><th>Status</th></tr></thead><tbody>{calculatedTrips.map((trip) => <tr key={trip.trip_id}><td>{trip.source} <small>to</small> {trip.destination}</td><td>{trip.route_type}</td><td>{kilometres(trip.planned_distance)}</td><td>{hours(trip.estimated_duration)}</td><td>{trip.eta ? new Date(trip.eta).toLocaleString() : "Not calculated"}</td><td><StatusBadge status={trip.status} /></td></tr>)}</tbody></table></div> : <EmptyState title="No calculated routes" description="Route distance and duration appear here after a trip route is calculated." />}</section></>);
}
export default LogisticsAnalytics;
