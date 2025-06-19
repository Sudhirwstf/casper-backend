import postgreDb from "../../config/db";
import { eq  } from "drizzle-orm"


import { generateAuthTokens } from "../../config/token";
import { users } from "../../models/schema";


export class auth{

    static generateId = () => Math.random().toString(36).substr(2, 8).toUpperCase();

      static googleLogIn = async (email: string, name: string,picture:string): Promise<any> => {
    try {
      const user: any = await postgreDb
        .select()
        .from(users)
        .where(eq(users.email, email))
        .limit(1);
      if (user.length <= 0) {
        
        const user: any = await postgreDb
          .insert(users)
          .values({
            name: name,
            email: email,
            phoneNumber: "null",
            password: "null",
            picture: picture
          })
          .returning();
        const token = generateAuthTokens({ userId: user[0].id });
        return { token: token, user: user[0] };
      }
      const token = generateAuthTokens({ userId: user[0].id });
      return { token, user: user[0] };
    } catch (error: any) {
      throw new Error(error);
    }
  };
    
      

       
  }