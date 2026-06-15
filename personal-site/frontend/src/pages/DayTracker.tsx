import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { todayISO, usePrivateToken } from "../lib/auth";
import {
  dayNumber,
  formatWeekLabel,
  mondayOf,
  shiftWeek,
  shortDay,
} from "../lib/week";
import PrivateShell from "../components/PrivateShell";
import type { DayEntry, WeekSummary } from "../lib/types";
import "./PrivatePages.css";

function formatEntryDate(iso: string): string {
  const d = new Date(iso + "T12:00:00");
  return d.toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric", year: "numeric" });
}

export default function DayTrackerPage() {
  const token = usePrivateToken();
  const today = todayISO();
  const [selectedDate, setSelectedDate] = useState(today);
  const [viewWeekStart, setViewWeekStart] = useState(mondayOf(today));
  const [personal, setPersonal] = useState("");
  const [professional, setProfessional] = useState("");
  const [entries, setEntries] = useState<DayEntry[]>([]);
  const [week, setWeek] = useState<WeekSummary | null>(null);
  const [weekSummaryEdit, setWeekSummaryEdit] = useState("");
  const [summarySaved, setSummarySaved] = useState(false);
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(true);

  const loadEntries = async () => {
    const list = await api.getDayEntries(token);
    setEntries(list);
  };

  const loadWeek = async (weekStart: string) => {
    const data = await api.getWeekSummary(token, weekStart);
    setWeek(data);
    setWeekSummaryEdit(data.summary);
  };

  const loadDay = async (date: string) => {
    setLoading(true);
    setSaved(false);
    try {
      const entry = await api.getDayEntry(token, date);
      setPersonal(entry.personal);
      setProfessional(entry.professional);
    } catch {
      setPersonal("");
      setProfessional("");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEntries().catch(() => {});
  }, [token]);

  useEffect(() => {
    setViewWeekStart(mondayOf(selectedDate));
  }, [selectedDate]);

  useEffect(() => {
    loadWeek(viewWeekStart).catch(() => {});
  }, [viewWeekStart, token]);

  useEffect(() => {
    loadDay(selectedDate);
  }, [selectedDate, token]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    await api.saveDayEntry(token, selectedDate, { personal, professional });
    setSaved(true);
    await Promise.all([loadEntries(), loadWeek(viewWeekStart)]);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleSaveSummary = async () => {
    await api.updateWeekSummary(token, viewWeekStart, weekSummaryEdit);
    await loadWeek(viewWeekStart);
    setSummarySaved(true);
    setTimeout(() => setSummarySaved(false), 2000);
  };

  const isToday = selectedDate === today;
  const currentWeekStart = mondayOf(today);

  return (
    <PrivateShell>
      <p className="section-label"><span>§</span> Private Day tracker</p>
      <h1 className="page-title serif">{isToday ? "Today." : formatEntryDate(selectedDate)}</h1>
      <p className="page-subtitle">
        What you accomplished — personal and professional. One honest record per day.
      </p>

      <section className="week-tracker card">
        <div className="week-tracker-header">
          <button
            type="button"
            className="week-nav-btn mono"
            onClick={() => setViewWeekStart(shiftWeek(viewWeekStart, -1))}
            aria-label="Previous week"
          >
            ←
          </button>
          <div className="week-tracker-title">
            <h2 className="mono">Week tracker</h2>
            <p className="week-tracker-range mono">
              {week ? formatWeekLabel(week.week_start, week.week_end) : ""}
            </p>
          </div>
          <button
            type="button"
            className="week-nav-btn mono"
            onClick={() => setViewWeekStart(shiftWeek(viewWeekStart, 1))}
            disabled={viewWeekStart >= currentWeekStart}
            aria-label="Next week"
          >
            →
          </button>
        </div>

        <div className="week-strip">
          {week?.days.map((day) => {
            const isSelected = day.entry_date === selectedDate;
            const isFuture = day.entry_date > today;
            return (
              <button
                key={day.entry_date}
                type="button"
                className={`week-day ${isSelected ? "selected" : ""} ${day.has_entry ? "filled" : ""} ${isFuture ? "future" : ""}`}
                onClick={() => !isFuture && setSelectedDate(day.entry_date)}
                disabled={isFuture}
              >
                <span className="week-day-name mono">{shortDay(day.entry_date)}</span>
                <span className="week-day-num">{dayNumber(day.entry_date)}</span>
                <span className={`week-day-dot ${day.has_entry ? "on" : ""}`} />
              </button>
            );
          })}
        </div>

        <p className="week-progress mono">
          {week ? `${week.filled_count} of 7 days logged` : "Loading week…"}
        </p>

        {week?.is_complete && (
          <div className="week-summary-block">
            <div className="week-summary-header">
              <h3 className="mono">Weekly summary</h3>
              <span className="week-summary-badge mono">7/7 complete</span>
            </div>
            <textarea
              className="week-summary-textarea"
              value={weekSummaryEdit}
              onChange={(e) => setWeekSummaryEdit(e.target.value)}
              rows={10}
            />
            <button type="button" className="btn btn-outline week-summary-save" onClick={handleSaveSummary}>
              {summarySaved ? "Summary saved ✓" : "Save summary"}
            </button>
          </div>
        )}

        {week && !week.is_complete && week.filled_count > 0 && (
          <p className="week-summary-pending mono">
            Log all 7 days this week to unlock your weekly summary ({7 - week.filled_count} remaining).
          </p>
        )}
      </section>

      <div className="day-date-row mono">
        <label>
          Date
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            max={today}
          />
        </label>
        {!isToday && (
          <button type="button" className="btn btn-outline" onClick={() => setSelectedDate(today)}>
            Jump to today
          </button>
        )}
      </div>

      {loading ? (
        <p className="mono private-muted">Loading…</p>
      ) : (
        <form className="day-form card" onSubmit={handleSave}>
          <label>
            <span className="day-label mono">Personal</span>
            <span className="day-hint">Health, relationships, rest, hobbies, life outside work</span>
            <textarea
              value={personal}
              onChange={(e) => setPersonal(e.target.value)}
              rows={5}
              placeholder="Morning run along the river. Called mom. Read for an hour before bed."
            />
          </label>
          <label>
            <span className="day-label mono">Professional</span>
            <span className="day-hint">Work shipped, learned, decided, or unblocked</span>
            <textarea
              value={professional}
              onChange={(e) => setProfessional(e.target.value)}
              rows={5}
              placeholder="Drafted the KV-cache piece. Reviewed a design doc. Fixed the deploy pipeline."
            />
          </label>
          <div className="day-form-actions">
            <button type="submit" className="btn btn-primary">
              {saved ? "Saved ✓" : "Save entry"}
            </button>
          </div>
        </form>
      )}

      <section className="day-history">
        <h2 className="mono day-history-title">Recent days</h2>
        {entries.length === 0 ? (
          <p className="mono private-muted">No entries yet. Start with today.</p>
        ) : (
          <div className="day-history-list">
            {entries.map((entry) => (
              <button
                key={entry.id}
                type="button"
                className={`day-history-item card ${entry.entry_date === selectedDate ? "active" : ""}`}
                onClick={() => setSelectedDate(entry.entry_date)}
              >
                <span className="mono day-history-date">{formatEntryDate(entry.entry_date)}</span>
                <div className="day-history-preview">
                  {entry.personal && (
                    <p><span className="mono">personal</span> {entry.personal.slice(0, 80)}{entry.personal.length > 80 ? "…" : ""}</p>
                  )}
                  {entry.professional && (
                    <p><span className="mono">work</span> {entry.professional.slice(0, 80)}{entry.professional.length > 80 ? "…" : ""}</p>
                  )}
                  {!entry.personal && !entry.professional && (
                    <p className="private-muted">Empty entry</p>
                  )}
                </div>
              </button>
            ))}
          </div>
        )}
      </section>

      <p className="private-footer-link">
        <Link to="/private/identity" className="mono">Who I am →</Link>
      </p>
    </PrivateShell>
  );
}
