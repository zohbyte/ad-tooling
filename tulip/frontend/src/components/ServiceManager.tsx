import { useState } from "react";
import {
  useGetServicesQuery,
  useAddServiceMutation,
  useDeleteServiceMutation,
} from "../api";

export function ServiceManager() {
  const [open, setOpen] = useState(false);
  const [port, setPort] = useState("");
  const [name, setName] = useState("");
  const { data: services, refetch } = useGetServicesQuery();
  const [addService] = useAddServiceMutation();
  const [deleteService] = useDeleteServiceMutation();

  const onAdd = async () => {
    const portNum = parseInt(port, 10);
    if (!portNum || !name.trim()) return;
    await addService({ port: portNum, name: name.trim() });
    setPort("");
    setName("");
    refetch();
  };

  const onDelete = async (servicePort: number) => {
    await deleteService(servicePort);
    refetch();
  };

  if (!open) {
    return (
      <button
        className="bg-blue-100 text-gray-800 rounded-md px-2 py-1"
        title="Manage services"
        onClick={() => setOpen(true)}
      >
        Services
      </button>
    );
  }

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.45)",
        zIndex: 50,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
      onClick={() => setOpen(false)}
    >
      <div
        className="bg-white text-gray-900 rounded-lg p-4"
        style={{ width: "420px", maxHeight: "80vh", overflow: "auto" }}
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="font-semibold mb-3">Services</h3>
        <p className="text-sm text-gray-600 mb-3">
          Add ports as you discover them. Used for filtering and flow labels.
        </p>
        <div className="flex gap-2 mb-3">
          <input
            className="border rounded px-2 py-1 w-24"
            placeholder="port"
            value={port}
            onChange={(e) => setPort(e.target.value)}
          />
          <input
            className="border rounded px-2 py-1 flex-1"
            placeholder="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <button className="bg-blue-500 text-white rounded px-3" onClick={onAdd}>
            Add
          </button>
        </div>
        <ul className="text-sm">
          {(services || []).map((s) => (
            <li key={`${s.ip}:${s.port}`} className="flex justify-between py-1 border-b">
              <span>
                {s.name} <span className="text-gray-500">:{s.port}</span>
              </span>
              <button
                className="text-red-600"
                onClick={() => onDelete(s.port)}
              >
                remove
              </button>
            </li>
          ))}
          {(!services || services.length === 0) && (
            <li className="text-gray-500 py-2">No services yet — add a port and name.</li>
          )}
        </ul>
        <button className="mt-4 text-sm underline" onClick={() => setOpen(false)}>
          Close
        </button>
      </div>
    </div>
  );
}
