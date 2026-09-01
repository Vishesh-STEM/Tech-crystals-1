import {
  Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, PolarAngleAxis, PolarGrid,
  PolarRadiusAxis, Radar, RadarChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { useTheme } from "../../context/ThemeContext";

const PALETTE = ["#3563f5", "#8b5cf6", "#10b981", "#f59e0b", "#ef4444", "#06b6d4", "#ec4899"];

function useAxisColors() {
  const { theme } = useTheme();
  const grid = theme === "dark" ? "rgba(255,255,255,0.08)" : "rgba(15,21,35,0.08)";
  const text = theme === "dark" ? "#8591aa" : "#667490";
  const tooltipStyle = {
    background: theme === "dark" ? "#0f1523" : "#ffffff",
    border: `1px solid ${theme === "dark" ? "rgba(255,255,255,0.1)" : "rgba(15,21,35,0.1)"}`,
    borderRadius: 12,
    fontSize: 12,
    color: theme === "dark" ? "#eceef2" : "#0f1523",
  };
  return { grid, text, tooltipStyle };
}

export function SubjectMasteryChart({ data }: { data: { subject_name: string; mastery: number }[] }) {
  const { grid, text, tooltipStyle } = useAxisColors();
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} margin={{ top: 8, right: 8, bottom: 8, left: -18 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={grid} vertical={false} />
        <XAxis
          dataKey="subject_name"
          tick={{ fill: text, fontSize: 11 }}
          tickLine={false}
          axisLine={false}
          interval={0}
          tickFormatter={(value: string) => (value.length > 9 ? `${value.slice(0, 8)}.` : value)}
        />
        <YAxis domain={[0, 100]} tick={{ fill: text, fontSize: 11 }} tickLine={false} axisLine={false} />
        <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "rgba(53,99,245,0.06)" }} formatter={(v: any) => [`${v}/100`, "Mastery"]} />
        <Bar dataKey="mastery" radius={[8, 8, 0, 0]} maxBarSize={46}>
          {data.map((entry, index) => (
            <Cell key={entry.subject_name} fill={PALETTE[index % PALETTE.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function ProgressLineChart({
  data,
  dataKey = "mastery",
  height = 240,
}: {
  data: any[];
  dataKey?: string;
  height?: number;
}) {
  const { grid, text, tooltipStyle } = useAxisColors();
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 8, right: 12, bottom: 8, left: -18 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={grid} vertical={false} />
        <XAxis dataKey="label" tick={{ fill: text, fontSize: 11 }} tickLine={false} axisLine={false} />
        <YAxis domain={[0, 100]} tick={{ fill: text, fontSize: 11 }} tickLine={false} axisLine={false} />
        <Tooltip contentStyle={tooltipStyle} formatter={(v: any) => [`${v}/100`, "Mastery"]} />
        <Line
          type="monotone"
          dataKey={dataKey}
          stroke="#3563f5"
          strokeWidth={2.5}
          dot={{ r: 4, fill: "#3563f5" }}
          activeDot={{ r: 6 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function LearningProfileRadar({ profile }: { profile: Record<string, number> }) {
  const { grid, text, tooltipStyle } = useAxisColors();
  const data = [
    { format: "Text", value: Math.round((profile.text_effectiveness || 0) * 100) },
    { format: "Visual", value: Math.round((profile.visual_effectiveness || 0) * 100) },
    { format: "Audio", value: Math.round((profile.audio_effectiveness || 0) * 100) },
    { format: "Practice", value: Math.round((profile.practice_effectiveness || 0) * 100) },
  ];
  return (
    <ResponsiveContainer width="100%" height={240}>
      <RadarChart data={data} outerRadius="72%">
        <PolarGrid stroke={grid} />
        <PolarAngleAxis dataKey="format" tick={{ fill: text, fontSize: 12 }} />
        <PolarRadiusAxis domain={[0, 100]} tick={{ fill: text, fontSize: 10 }} axisLine={false} />
        <Tooltip contentStyle={tooltipStyle} formatter={(v: any) => [`${v}%`, "Effectiveness"]} />
        <Radar dataKey="value" stroke="#3563f5" fill="#3563f5" fillOpacity={0.28} />
      </RadarChart>
    </ResponsiveContainer>
  );
}

export function ActivityBarChart({ data }: { data: { date?: string; label?: string; events?: number; minutes?: number }[] }) {
  const { grid, text, tooltipStyle } = useAxisColors();
  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={data} margin={{ top: 8, right: 8, bottom: 8, left: -22 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={grid} vertical={false} />
        <XAxis
          dataKey={data[0]?.label ? "label" : "date"}
          tick={{ fill: text, fontSize: 10 }}
          tickLine={false}
          axisLine={false}
          tickFormatter={(value: string) => (value?.length > 5 ? value.slice(5) : value)}
        />
        <YAxis tick={{ fill: text, fontSize: 10 }} tickLine={false} axisLine={false} />
        <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "rgba(53,99,245,0.06)" }} />
        <Bar dataKey={data[0]?.minutes !== undefined ? "minutes" : "events"} fill="#3563f5" radius={[6, 6, 0, 0]} maxBarSize={22} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function DifficultyBars({ data }: { data: { name: string; accuracy: number }[] }) {
  const { grid, text, tooltipStyle } = useAxisColors();
  return (
    <ResponsiveContainer width="100%" height={180}>
      <BarChart data={data} layout="vertical" margin={{ top: 4, right: 16, bottom: 4, left: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={grid} horizontal={false} />
        <XAxis type="number" domain={[0, 100]} tick={{ fill: text, fontSize: 11 }} axisLine={false} tickLine={false} />
        <YAxis type="category" dataKey="name" tick={{ fill: text, fontSize: 12 }} axisLine={false} tickLine={false} width={70} />
        <Tooltip contentStyle={tooltipStyle} formatter={(v: any) => [`${v}%`, "Accuracy"]} />
        <Bar dataKey="accuracy" radius={[0, 8, 8, 0]} maxBarSize={22}>
          {data.map((entry, index) => (
            <Cell key={entry.name} fill={PALETTE[index % PALETTE.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
