import { useState, useEffect } from 'react';
import { onSnapshot, doc } from 'firebase/firestore';
import { db } from '@/lib/firebase';
import { useAuthStore } from '@/stores/auth-store';

export type Rank = {
    rank: number;
    label: string;
    currentScore: number;
    totalSubmissions: number;
    highScores: number[];
};

const getRankLabel = (rankValue: number): string => {
    if (rankValue <= 10) {
        return `${11 - rankValue}級`;
    } else if (rankValue <= 13) {
        return `${rankValue - 10}段`;
    } else if (rankValue === 14) {
        return "師範代";
    } else {
        return "師範";
    }
};

export const useRank = () => {
    const { user } = useAuthStore();
    const [rank, setRank] = useState<Rank | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!user) {
            // ユーザーがいない場合は初期状態のままにする
            return;
        }

        // onSnapshotのコールバック内でsetStateを呼ぶのは正しいパターン
        // ユーザーランクは 'users/{userId}' ドキュメントに保存されている想定
        const userRef = doc(db, 'users', user.uid);

        const unsubscribe = onSnapshot(
            userRef,
            (docSnapshot) => {
                if (docSnapshot.exists()) {
                    const data = docSnapshot.data();
                    const rankValue = data.rank as number || 1; // Default to 1 (10級) if missing

                    setRank({
                        rank: rankValue,
                        label: getRankLabel(rankValue),
                        currentScore: data.latest_score as number || 0,
                        totalSubmissions: data.total_submissions as number || 0,
                        highScores: data.high_scores as number[] || [],
                    });
                } else {
                    // ドキュメントがない場合は初期ランクとみなす
                    setRank({
                        rank: 1,
                        label: getRankLabel(1),
                        currentScore: 0,
                        totalSubmissions: 0,
                        highScores: [],
                    });
                }
                setLoading(false);
            },
            (err) => {
                console.error('Error fetching rank:', err);
                setError(err.message);
                setLoading(false);
            }
        );

        return () => unsubscribe();
    }, [user]);

    return { rank, loading, error };
};
