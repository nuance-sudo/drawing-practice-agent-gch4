import { SignJWT } from 'jose';

const SECRET_KEY = new TextEncoder().encode(
    process.env.NEXT_PUBLIC_AUTH_SECRET || 'hackathon-secret-123'
);

export async function createToken(userId: string) {
    return new SignJWT({ sub: userId })
        .setProtectedHeader({ alg: 'HS256' })
        .setIssuedAt()
        .sign(SECRET_KEY);
}

// クライアントサイドでトークンを取得するための簡易フック/関数
// 本来はServer ActionやAuth.jsのセッションから取得するが、
// ハッカソン構成として、localStorageまたは固定のテストユーザーIDから生成する
export async function getAuthToken() {
    // 開発/デモ用: 常に固定ユーザーのトークンを返す
    // 本番ではログインフローが必要
    return createToken('user-1');
}
