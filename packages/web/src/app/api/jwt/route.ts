import { auth } from "@/auth";
import { SignJWT } from "jose";

const SECRET_KEY = new TextEncoder().encode(
  process.env.NEXT_PUBLIC_AUTH_SECRET || 'hackathon-secret-123'
);

export async function GET(req: Request) {
  const session = await auth();

  if (!session || !session.user?.id) {
    return Response.json({ error: "Unauthorized" }, { status: 401 });
  }

  // バックエンド用のJWTを生成
  // backend/src/auth/dependencies.py の検証ロジックに合わせる
  const token = await new SignJWT({ 
      sub: session.user.id,
      email: session.user.email 
    })
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt()
    .sign(SECRET_KEY);

  return Response.json({ token });
}
