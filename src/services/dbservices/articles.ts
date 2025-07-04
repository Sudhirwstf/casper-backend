import { eq, sql } from "drizzle-orm";
import postgreDb from "../../config/db";
import { articles, users } from "../../models/schema";

export class ArticleServices {
  static saveArticles = async (textFiles:any,userId: number) => {
    // Validate userId is a number
    if (isNaN(userId)) throw new Error("User ID is NaN");

    const result = await postgreDb.transaction(async (tx) => {
      const creditUsed = textFiles.length * 5;

      // Insert all articles
      for (const file of textFiles) {
        if (!file.filename || !file.content) {
          throw new Error("Missing filename or content");
        }
      

        await tx.insert(articles).values({
          userId: Number(userId), 
          filename: file.filename,
          aiGeneratedPost: file.content,
        });
      }
     

      // Deduct credits
      await tx
      .update(users)
      .set({
        credits: sql`${users.credits} - ${creditUsed}`,
      })
      .where(eq(users.id, userId));


     
      // Fetch updated user credits
      const [updatedUser] = await tx
        .select({ credits: users.credits })
        .from(users)
        .where(eq(users.id, userId));
          console.log("done")

      return {
        success: true,
        remainingCredits: updatedUser.credits,
      };
    });

    return result;
  };



  static generateImage=async():Promise<any>=>{
    try{
       
     
    }catch(error:any){
        throw new Error(error)
    }
  }

  static checkEnoughCredits=async(userId: number):Promise<any>=>{
    try{
        const [user] = await postgreDb
        .select({ credits:users.credits })
        .from(users)
        .where(eq(users.id, userId));
        console.log(user.credits,"db")
        return user.credits
    }catch(error:any){
        throw new Error(error)
    }
  }

  static deductCredits=async(userId: number,amount:number):Promise<any>=>{
    try{
        await postgreDb
        .update(users)
        .set({
          credits: sql`${users.credits} - ${amount}`,
        })
        .where(eq(users.id, userId));
    }catch(error:any){
        throw new Error(error)
    }
  }
}
