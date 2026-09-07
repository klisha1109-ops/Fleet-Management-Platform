import { useCallback, useContext, useEffect, useMemo, useState } from "react";
import { Navigate } from "react-router-dom";
import EmptyState from "../components/EmptyState";
import LoadingCard from "../components/LoadingCard";
import MainLayout from "../layouts/MainLayout";
import PageHeader from "../components/PageHeader";
import SearchBar from "../components/SearchBar";
import api from "../services/api";
import { AuthContext } from "../context/auth-context";
import "./UserManagement.css";

const roles = ["Admin", "FleetManager", "Dispatcher", "Driver"];
const roleLabels = { Admin: "Administrator", FleetManager: "Fleet Manager", Dispatcher: "Dispatcher", Driver: "Driver" };
const blankForm = { full_name: "", email: "", password: "", phone: "", address: "", role: "Driver" };

function UserManagement() {
  const { user } = useContext(AuthContext);
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [role, setRole] = useState("");
  const [active, setActive] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [form, setForm] = useState(null);
  const [saving, setSaving] = useState(false);
  const canManage = user?.role === "Admin";

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const response = await api.get("/users", { params: { limit: 100, ...(search ? { search } : {}), ...(role ? { role } : {}), ...(active ? { is_active: active === "active" } : {}) } });
      setItems(response.data.items || []); setTotal(response.data.total || 0);
    } catch (requestError) { setError(requestError.response?.data?.detail || "Unable to load users."); }
    finally { setLoading(false); }
  }, [active, role, search]);

  useEffect(() => {
    if (!canManage) return undefined;
    const requestId = window.setTimeout(() => { void load(); }, 0);
    return () => window.clearTimeout(requestId);
  }, [canManage, load]);
  const counts = useMemo(() => roles.reduce((result, item) => ({ ...result, [item]: items.filter((value) => value.role === item).length }), {}), [items]);
  const change = (name, value) => setForm((current) => ({ ...current, [name]: value }));
  const save = async (event) => {
    event.preventDefault(); setSaving(true); setError("");
    try {
      if (form.user_id) {
        await api.put(`/users/${form.user_id}`, { full_name: form.full_name, email: form.email, phone: form.phone || null, address: form.address || null, role: form.role });
        setNotice("User updated successfully.");
      } else { await api.post("/users", form); setNotice("User created successfully."); }
      setForm(null); await load();
    } catch (requestError) { setError(requestError.response?.data?.detail || "Unable to save user."); }
    finally { setSaving(false); }
  };
  const toggle = async (target) => {
    setSaving(true); setError("");
    try { await api.patch(`/users/${target.user_id}/status`, { is_active: !target.is_active }); setNotice(`${target.full_name} was ${target.is_active ? "deactivated" : "activated"}.`); await load(); }
    catch (requestError) { setError(requestError.response?.data?.detail || "Unable to change account status."); }
    finally { setSaving(false); }
  };
  if (user && !canManage) return <Navigate to="/dashboard" replace />;
  if (loading) return <MainLayout><LoadingCard message="Loading users..." /></MainLayout>;
  return <MainLayout>
    <PageHeader eyebrow="Administration" title="User Management" description="Manage FleetFlow users, roles and account access." />
    <div className="um-actions"><button className="primary-button" onClick={() => setForm(blankForm)}>Add User</button><button onClick={() => void load()} disabled={saving}>Refresh</button></div>
    {notice && <p className="um-notice">{notice}</p>}{error && <p className="um-error">{error}</p>}
    <div className="um-summary">{[["Total Users", total], ["Administrators", counts.Admin], ["Fleet Managers", counts.FleetManager], ["Dispatchers", counts.Dispatcher], ["Drivers", counts.Driver], ["Active Users", items.filter((item) => item.is_active).length]].map(([label, value]) => <article key={label}><span>{label}</span><strong>{value}</strong></article>)}</div>
    <div className="um-filters"><SearchBar value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search name, email or phone" /><select value={role} onChange={(event) => setRole(event.target.value)}><option value="">All roles</option>{roles.map((item) => <option key={item} value={item}>{roleLabels[item]}</option>)}</select><select value={active} onChange={(event) => setActive(event.target.value)}><option value="">All statuses</option><option value="active">Active</option><option value="inactive">Inactive</option></select></div>
    {!items.length ? <EmptyState title="No users found" description="Try another search or filter." /> : <div className="um-table"><table><thead><tr><th>Name</th><th>Email</th><th>Phone</th><th>Role</th><th>Status</th><th>Created</th><th>Actions</th></tr></thead><tbody>{items.map((item) => <tr key={item.user_id}><td>{item.full_name}</td><td>{item.email}</td><td>{item.phone || "—"}</td><td>{roleLabels[item.role]}</td><td>{item.is_active ? "Active" : "Inactive"}</td><td>{item.created_at ? new Date(item.created_at).toLocaleDateString() : "—"}</td><td><button onClick={() => setForm({ ...item, password: "" })} disabled={saving}>Edit</button><button onClick={() => void toggle(item)} disabled={saving}>{item.is_active ? "Deactivate" : "Activate"}</button></td></tr>)}</tbody></table></div>}
    {form && <div className="um-modal"><form onSubmit={save}><h2>{form.user_id ? "Edit User" : "Add User"}</h2><label>Full Name<input required value={form.full_name} onChange={(event) => change("full_name", event.target.value)} /></label><label>Email<input required type="email" value={form.email} onChange={(event) => change("email", event.target.value)} /></label>{!form.user_id && <label>Password<input required minLength="8" type="password" value={form.password} onChange={(event) => change("password", event.target.value)} /></label>}<label>Phone<input value={form.phone || ""} onChange={(event) => change("phone", event.target.value)} /></label><label>Address<textarea value={form.address || ""} onChange={(event) => change("address", event.target.value)} /></label><label>Role<select value={form.role} onChange={(event) => change("role", event.target.value)}>{roles.map((item) => <option key={item} value={item}>{roleLabels[item]}</option>)}</select></label><div><button type="button" onClick={() => setForm(null)} disabled={saving}>Cancel</button><button className="primary-button" disabled={saving}>{saving ? "Saving..." : "Save"}</button></div></form></div>}
  </MainLayout>;
}

export default UserManagement;
