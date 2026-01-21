'use client';

import { useSyncExternalStore, useCallback, useRef, useEffect } from 'react';
import {
    collection,
    onSnapshot,
    query,
    where,
    orderBy,
    doc,
    DocumentData,
    QuerySnapshot,
    DocumentSnapshot,
} from 'firebase/firestore';
import { db } from '@/lib/firebase';
import type { ReviewTask, TaskStatus } from '@/types/task';

/**
 * Firestoreのドキュメントデータを ReviewTask 型に変換
 */
// Firestoreからの生データ型（概略）
interface FirestoreFeedback {
    overall_score: number;
    strengths: string[];
    improvements: string[];
    proportion?: { score: number; comments?: string[] };
    tone?: { score: number; comments?: string[] };
    texture?: { score: number; comments?: string[] };
    line_quality?: { score: number; comments?: string[] };
}

const mapDocToTask = (docSnapshot: DocumentSnapshot<DocumentData>): ReviewTask => {
    const data = docSnapshot.data();
    if (!data) {
        throw new Error('Document data is undefined');
    }

    // Feedbackデータの変換
    let feedback = undefined;
    if (data.feedback) {
        const fb = data.feedback as FirestoreFeedback;
        // 必須フィールドのチェック（簡易的）
        if (fb.overall_score !== undefined && fb.strengths && fb.improvements) {
            feedback = {
                overallScore: fb.overall_score,
                strengths: fb.strengths,
                improvements: fb.improvements,
                details: {
                    proportion: {
                        score: fb.proportion?.score ?? 0,
                        comments: [], // コメントは現状APIから返ってこない場合があるため空配列でフォールバック
                    },
                    shading: {
                        score: fb.tone?.score ?? 0, // tone -> shading
                        comments: [],
                    },
                    lineQuality: {
                        score: fb.line_quality?.score ?? 0, // line_quality -> lineQuality
                        comments: [],
                    },
                },
            };
        }
    }

    return {
        taskId: docSnapshot.id,
        userId: data.user_id as string,
        status: data.status as TaskStatus,
        imageUrl: data.image_url as string,
        exampleImageUrl: data.example_image_url as string | undefined,
        feedback: feedback,
        score: data.score as number | undefined,
        tags: data.tags as string[] | undefined,
        errorMessage: data.error_message as string | undefined,
        createdAt: data.created_at?.toDate?.()?.toISOString() ?? new Date().toISOString(),
        updatedAt: data.updated_at?.toDate?.()?.toISOString() ?? new Date().toISOString(),
    };
};

type TasksState = {
    tasks: ReviewTask[];
    isLoading: boolean;
    error: Error | null;
};

type SingleTaskState = {
    task: ReviewTask | null;
    isLoading: boolean;
    error: Error | null;
};

/**
 * Firestoreからタスクをリアルタイム監視するカスタムフック
 * エージェントがタスクステータスを更新した瞬間にUIに反映される
 */
export const useTasks = (userId: string | null): TasksState => {
    const stateRef = useRef<TasksState>({
        tasks: [],
        isLoading: !!userId,
        error: null,
    });
    const listenersRef = useRef(new Set<() => void>());

    const subscribe = useCallback((callback: () => void) => {
        listenersRef.current.add(callback);
        return () => listenersRef.current.delete(callback);
    }, []);

    const getSnapshot = useCallback(() => stateRef.current, []);

    const notifyListeners = useCallback(() => {
        listenersRef.current.forEach((listener) => listener());
    }, []);

    useEffect(() => {
        if (!userId) {
            stateRef.current = { tasks: [], isLoading: false, error: null };
            notifyListeners();
            return;
        }

        stateRef.current = { ...stateRef.current, isLoading: true, error: null };
        notifyListeners();

        const q = query(
            collection(db, 'review_tasks'),
            where('user_id', '==', userId),
            orderBy('created_at', 'desc')
        );

        const unsubscribe = onSnapshot(
            q,
            (snapshot: QuerySnapshot<DocumentData>) => {
                const newTasks: ReviewTask[] = snapshot.docs.map((docSnapshot) =>
                    mapDocToTask(docSnapshot as DocumentSnapshot<DocumentData>)
                );
                stateRef.current = { tasks: newTasks, isLoading: false, error: null };
                notifyListeners();
            },
            (err) => {
                console.error('Firestore realtime listener error:', err);
                stateRef.current = { tasks: [], isLoading: false, error: err };
                notifyListeners();
            }
        );

        return () => unsubscribe();
    }, [userId, notifyListeners]);

    return useSyncExternalStore(subscribe, getSnapshot, getSnapshot);
};

/**
 * 単一タスクをリアルタイム監視するカスタムフック
 */
export const useTask = (taskId: string | null): SingleTaskState => {
    const stateRef = useRef<SingleTaskState>({
        task: null,
        isLoading: !!taskId,
        error: null,
    });
    const listenersRef = useRef(new Set<() => void>());

    const subscribe = useCallback((callback: () => void) => {
        listenersRef.current.add(callback);
        return () => listenersRef.current.delete(callback);
    }, []);

    const getSnapshot = useCallback(() => stateRef.current, []);

    const notifyListeners = useCallback(() => {
        listenersRef.current.forEach((listener) => listener());
    }, []);

    useEffect(() => {
        if (!taskId) {
            stateRef.current = { task: null, isLoading: false, error: null };
            notifyListeners();
            return;
        }

        stateRef.current = { ...stateRef.current, isLoading: true, error: null };
        notifyListeners();

        const docRef = doc(db, 'review_tasks', taskId);

        const unsubscribe = onSnapshot(
            docRef,
            (snapshot: DocumentSnapshot<DocumentData>) => {
                if (snapshot.exists()) {
                    stateRef.current = { task: mapDocToTask(snapshot), isLoading: false, error: null };
                } else {
                    stateRef.current = { task: null, isLoading: false, error: null };
                }
                notifyListeners();
            },
            (err) => {
                console.error('Firestore single doc listener error:', err);
                stateRef.current = { task: null, isLoading: false, error: err };
                notifyListeners();
            }
        );

        return () => unsubscribe();
    }, [taskId, notifyListeners]);

    return useSyncExternalStore(subscribe, getSnapshot, getSnapshot);
};
