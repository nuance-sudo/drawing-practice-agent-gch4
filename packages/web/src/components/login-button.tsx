"use client";

import { Github } from "lucide-react";
import { signInWithPopup, GithubAuthProvider, signOut } from "firebase/auth";
import { auth } from "@/lib/firebase";
import { useAuthStore } from "@/stores/auth-store";

export function LoginButton() {
    const { user, loading } = useAuthStore();

    const handleLogin = async () => {
        try {
            const provider = new GithubAuthProvider();
            await signInWithPopup(auth, provider);
        } catch (error) {
            console.error("Login failed:", error);
            alert("Login failed");
        }
    };

    const handleLogout = async () => {
        try {
            await signOut(auth);
        } catch (error) {
            console.error("Logout failed:", error);
        }
    };

    if (loading) {
        return <button className="px-4 py-2 text-gray-500">Loading...</button>;
    }

    if (user) {
        return (
            <div className="flex items-center gap-4">
                <span className="text-sm">Logged in as {user.displayName}</span>
                <button
                    onClick={handleLogout}
                    className="px-4 py-2 text-sm font-medium text-red-600 bg-red-50 rounded-md hover:bg-red-100"
                >
                    Logout
                </button>
            </div>
        );
    }

    return (
        <button
            onClick={handleLogin}
            className="flex items-center gap-2 px-4 py-2 text-white bg-gray-900 rounded-md hover:bg-gray-800 transition-colors"
        >
            <Github className="w-5 h-5" />
            <span>Sign in with GitHub</span>
        </button>
    );
}
