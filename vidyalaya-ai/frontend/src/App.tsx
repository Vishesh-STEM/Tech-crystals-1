import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import { RequireAuth, RequireStaff } from "./components/Guards";
import About from "./pages/About";
import Chat from "./pages/Chat";
import ChapterDetail from "./pages/ChapterDetail";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";
import NotFound from "./pages/NotFound";
import Profile from "./pages/Profile";
import Progress from "./pages/Progress";
import Quiz from "./pages/Quiz";
import Quizzes from "./pages/Quizzes";
import Recommendations from "./pages/Recommendations";
import Register from "./pages/Register";
import Settings from "./pages/Settings";
import SubjectDetail from "./pages/SubjectDetail";
import Subjects from "./pages/Subjects";
import TopicDetail from "./pages/TopicDetail";
import AdminAnalytics from "./pages/admin/AdminAnalytics";
import AdminCatalog from "./pages/admin/AdminCatalog";
import AdminHome from "./pages/admin/AdminHome";
import AdminQuestions from "./pages/admin/AdminQuestions";
import AdminQuizzes from "./pages/admin/AdminQuizzes";
import AdminStudents from "./pages/admin/AdminStudents";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/about" element={<About />} />

      <Route
        element={
          <RequireAuth>
            <Layout />
          </RequireAuth>
        }
      >
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/subjects" element={<Subjects />} />
        <Route path="/subjects/:subjectId" element={<SubjectDetail />} />
        <Route path="/chapters/:chapterId" element={<ChapterDetail />} />
        <Route path="/topics/:topicId" element={<TopicDetail />} />
        <Route path="/quizzes" element={<Quizzes />} />
        <Route path="/quiz/:quizId" element={<Quiz />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/progress" element={<Progress />} />
        <Route path="/recommendations" element={<Recommendations />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/settings" element={<Settings />} />

        <Route
          path="/admin"
          element={
            <RequireStaff>
              <AdminHome />
            </RequireStaff>
          }
        />
        <Route
          path="/admin/students"
          element={
            <RequireStaff>
              <AdminStudents />
            </RequireStaff>
          }
        />
        <Route
          path="/admin/subjects"
          element={
            <RequireStaff>
              <AdminCatalog entity="subjects" />
            </RequireStaff>
          }
        />
        <Route
          path="/admin/chapters"
          element={
            <RequireStaff>
              <AdminCatalog entity="chapters" />
            </RequireStaff>
          }
        />
        <Route
          path="/admin/topics"
          element={
            <RequireStaff>
              <AdminCatalog entity="topics" />
            </RequireStaff>
          }
        />
        <Route
          path="/admin/resources"
          element={
            <RequireStaff>
              <AdminCatalog entity="resources" />
            </RequireStaff>
          }
        />
        <Route
          path="/admin/questions"
          element={
            <RequireStaff>
              <AdminQuestions />
            </RequireStaff>
          }
        />
        <Route
          path="/admin/quizzes"
          element={
            <RequireStaff>
              <AdminQuizzes />
            </RequireStaff>
          }
        />
        <Route
          path="/admin/analytics"
          element={
            <RequireStaff>
              <AdminAnalytics />
            </RequireStaff>
          }
        />
      </Route>

      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
