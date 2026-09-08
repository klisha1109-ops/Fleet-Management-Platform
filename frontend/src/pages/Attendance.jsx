import { useCallback, useContext, useEffect, useMemo, useState } from "react";
import MainLayout from "../layouts/MainLayout";
import EmptyState from "../components/EmptyState";
import LoadingCard from "../components/LoadingCard";
import PageHeader from "../components/PageHeader";
import StatusBadge from "../components/StatusBadge";
import { AuthContext } from "../context/auth-context";
import api from "../services/api";
import "./Attendance.css";

const managementRoles = ["Admin", "FleetManager"];
const attendanceStatuses = ["Present", "Leave", "Absent"];
const todayIso = () => new Date(Date.now() - new Date().getTimezoneOffset() * 60000).toISOString().slice(0, 10);
const formatDate = (value) => value ? new Date(`${value}T00:00:00`).toLocaleDateString() : "—";

function Attendance() {
  const { user } = useContext(AuthContext);
  const canManage = managementRoles.includes(user?.role);
  const isDriver = user?.role === "Driver";
  const canViewDrivers = ["Admin", "FleetManager", "Dispatcher"].includes(user?.role);
  const [drivers, setDrivers] = useState([]); const [records, setRecords] = useState([]);
  const [selectedDate, setSelectedDate] = useState(todayIso());
  const [form, setForm] = useState({ driver_id: "", date: todayIso(), status: "Present", notes: "" });
  const [loading, setLoading] = useState(true); const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(""); const [message, setMessage] = useState("");
  const driverNames = useMemo(() => new Map(drivers.map((driver) => [driver.driver_id, driver.full_name || driver.driver_id])), [drivers]);
  const load = useCallback(async (date = selectedDate) => {
    setLoading(true); setError("");
    try {
      if (isDriver) { const response = await api.get("/attendance/me/history"); setRecords(Array.isArray(response.data) ? response.data : []); setDrivers([]); return; }
      const requests = [api.get("/attendance/fleet", { params: { date_value: date } })];
      if (canViewDrivers) requests.push(api.get("/drivers/"));
      const results = await Promise.all(requests);
      setRecords(Array.isArray(results[0].data) ? results[0].data : []);
      if (canViewDrivers) setDrivers(Array.isArray(results[1].data) ? results[1].data : []);
    } catch (requestError) { setError(requestError.response?.data?.detail || "Unable to load attendance records."); }
    finally { setLoading(false); }
  }, [canViewDrivers, isDriver, selectedDate]);
  useEffect(() => { const timer = window.setTimeout(() => { void load(); }, 0); return () => window.clearTimeout(timer); }, [load]);
  const submit = async (event) => {
    event.preventDefault(); setSubmitting(true); setMessage(""); setError("");
    try { await api.post("/attendance/mark", { ...form, notes: form.notes.trim() || null }); setMessage("Attendance saved successfully."); if (form.date === selectedDate) await load(); else setSelectedDate(form.date); }
    catch (requestError) { setError(requestError.response?.data?.detail || "Unable to save attendance."); }
    finally { setSubmitting(false); }
  };
  if (loading) return <MainLayout><LoadingCard message="Loading attendance records..." /></MainLayout>;
  return <MainLayout><PageHeader eyebrow={canManage ? "Fleet Operations" : "Operations"} title={canManage ? "Attendance Tracking" : isDriver ? "My Attendance History" : "Attendance Records"} description={canManage ? "Mark and review driver attendance by date." : isDriver ? "Review only the attendance records marked for you." : "Attendance visibility for operational planning."} />
    {error && <p className="attendance-error" role="alert">{error}</p>}{message && <p className="attendance-success" role="status">{message}</p>}
    {canManage && <section className="attendance-panel attendance-form-panel"><div className="attendance-panel-heading"><div><p>Daily attendance</p><h2>Mark attendance</h2></div></div><form className="attendance-form" onSubmit={submit}><label>Driver<select required value={form.driver_id} onChange={(event) => setForm({ ...form, driver_id: event.target.value })}><option value="">Select driver</option>{drivers.map((driver) => <option key={driver.driver_id} value={driver.driver_id}>{driver.full_name} · {driver.license_number || driver.driver_id}</option>)}</select></label><label>Date<input type="date" required value={form.date} onChange={(event) => { const date = event.target.value; setForm({ ...form, date }); setSelectedDate(date); }} /></label><label>Status<select value={form.status} onChange={(event) => setForm({ ...form, status: event.target.value })}>{attendanceStatuses.map((item) => <option key={item} value={item}>{item}</option>)}</select></label><label className="attendance-notes">Notes<textarea value={form.notes} maxLength="500" placeholder="Optional roster note" onChange={(event) => setForm({ ...form, notes: event.target.value })} /></label><button className="primary-button attendance-submit" type="submit" disabled={submitting || !form.driver_id}>{submitting ? "Saving..." : "Save Attendance"}</button></form></section>}
    <section className="attendance-panel"><div className="attendance-panel-heading"><div><p>{isDriver ? "My attendance" : "Attendance register"}</p><h2>{isDriver ? "Attendance history" : formatDate(selectedDate)}</h2></div>{!isDriver && <label className="attendance-filter">View date<input type="date" value={selectedDate} onChange={(event) => setSelectedDate(event.target.value)} /></label>}</div>{records.length ? <div className="attendance-table-wrap"><table><thead><tr>{!isDriver && <><th>Driver</th><th>Operational status</th></>}<th>Date</th><th>Attendance</th><th>Notes</th></tr></thead><tbody>{records.map((record) => { const driver = drivers.find((item) => item.driver_id === record.driver_id); return <tr key={record.attendance_id}>{!isDriver && <><td>{driver?.full_name || driverNames.get(record.driver_id) || record.driver_id}</td><td>{driver ? <StatusBadge status={driver.status} /> : "—"}</td></>}<td>{formatDate(record.date)}</td><td><StatusBadge status={record.status} /></td><td>{record.notes || "—"}</td></tr>; })}</tbody></table></div> : <EmptyState title="No attendance records" description={isDriver ? "No attendance has been marked for you yet." : "No attendance has been marked for this date."} />}</section>
  </MainLayout>;
}

export default Attendance;
