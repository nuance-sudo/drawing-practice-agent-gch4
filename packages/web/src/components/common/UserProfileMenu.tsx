'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { User, LogOut, Award, ChevronDown } from 'lucide-react';
import { signOut } from 'firebase/auth';
import { auth } from '@/lib/firebase';
import { useAuthStore } from '@/stores/auth-store';
import { useRank } from '@/hooks/useRank';

export const UserProfileMenu = () => {
    const { user } = useAuthStore();
    const { rank, loading } = useRank();
    const [isOpen, setIsOpen] = useState(false);
    const menuRef = useRef<HTMLDivElement>(null);

    const handleClickOutside = useCallback((event: MouseEvent) => {
        if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
            setIsOpen(false);
        }
    }, []);

    useEffect(() => {
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, [handleClickOutside]);

    const handleLogout = useCallback(async () => {
        try {
            await signOut(auth);
            setIsOpen(false);
        } catch (error) {
            console.error('Logout failed:', error);
        }
    }, []);

    if (!user) return null;

    return (
        <div className="relative" ref={menuRef}>
            {/* Profile Button */}
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="flex items-center gap-3 px-3 py-2 rounded-full bg-white border border-slate-200 hover:border-slate-300 hover:shadow-sm transition-all duration-200"
            >
                {user.photoURL ? (
                    <img
                        src={user.photoURL}
                        alt={user.displayName ?? 'User'}
                        className="w-8 h-8 rounded-full object-cover"
                    />
                ) : (
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                        <User className="w-4 h-4 text-white" />
                    </div>
                )}
                <div className="hidden sm:flex flex-col items-start">
                    <span className="text-sm font-medium text-slate-700 max-w-[100px] truncate">
                        {user.displayName ?? 'ユーザー'}
                    </span>
                    {loading ? (
                        <span className="text-xs text-slate-400">読込中...</span>
                    ) : (
                        <span className="text-xs font-semibold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                            {rank?.label ?? '10級'}
                        </span>
                    )}
                </div>
                <ChevronDown className={`w-4 h-4 text-slate-500 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
            </button>

            {/* Dropdown Menu */}
            {isOpen && (
                <div className="absolute right-0 mt-2 w-64 bg-white rounded-2xl shadow-lg border border-slate-200 overflow-hidden z-50 animate-in fade-in slide-in-from-top-2 duration-200">
                    {/* User Info */}
                    <div className="px-4 py-3 bg-gradient-to-br from-indigo-50 to-purple-50 border-b border-slate-100">
                        <div className="flex items-center gap-3">
                            {user.photoURL ? (
                                <img
                                    src={user.photoURL}
                                    alt={user.displayName ?? 'User'}
                                    className="w-10 h-10 rounded-full object-cover ring-2 ring-white shadow-sm"
                                />
                            ) : (
                                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center ring-2 ring-white shadow-sm">
                                    <User className="w-5 h-5 text-white" />
                                </div>
                            )}
                            <div className="flex-1 min-w-0">
                                <p className="font-semibold text-slate-900 truncate">
                                    {user.displayName ?? 'ユーザー'}
                                </p>
                                <p className="text-xs text-slate-500 truncate">
                                    {user.email}
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Rank Display */}
                    <div className="px-4 py-3 border-b border-slate-100">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2 text-slate-600">
                                <Award className="w-4 h-4 text-amber-500" />
                                <span className="text-sm">現在のランク</span>
                            </div>
                            {loading ? (
                                <div className="h-5 w-12 bg-slate-100 rounded animate-pulse" />
                            ) : (
                                <span className="font-bold text-lg bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                                    {rank?.label ?? '10級'}
                                </span>
                            )}
                        </div>
                        {rank && !loading && (
                            <div className="mt-2 text-xs text-slate-500">
                                投稿数: {rank.totalSubmissions} 回
                            </div>
                        )}
                    </div>

                    {/* Logout Button */}
                    <div className="p-2">
                        <button
                            onClick={handleLogout}
                            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
                        >
                            <LogOut className="w-4 h-4" />
                            ログアウト
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};
