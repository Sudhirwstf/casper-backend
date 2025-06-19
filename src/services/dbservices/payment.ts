// import {and, desc, eq, inArray, sql} from "drizzle-orm";
// import Razorpay from "razorpay";
// import { envConfigs } from "../../config/envconfig";
// import { Cashfree } from "cashfree-pg";
// import logger from "../../config/logger";

// Cashfree.XClientId = envConfigs.xclientId
// Cashfree.XClientSecret = envConfigs.xclientSecret
// Cashfree.XEnvironment = Cashfree.Environment.SANDBOX;   // test mode = SANDBOX , and  development mode = PRODUC

// export class Payment{

//     static getUserDetails = async(userId:number):Promise<any>=>{
//         try{

//         }catch(error:any){
//            throw new Error
//         }        
//     }

//     static insertPaymentDetails = async(details:any):Promise<any>=>{
//         try{

//         }catch(error){
//             throw new error
//         }
//     }

//     static confirmOrderStatus = async(orderId: any, status : string):Promise<any>=>{
//         try{
//    // logic to confirm order and update details
//         }catch(error){
//             throw new error
//         }
//     }


//     static updateOrderStatus = async(orderId: any, status : string):Promise<any>=>{
//         try{
//    // logic to failure status order and update details
//         }catch(error){
//             throw new error
//         }
//     }

// static createPayment=async(amount:number,currency:string):Promise<any>=>{
//     try {
//         const instance = new Razorpay({
//         key_id:envConfigs.razorpayApiKey ,
//         key_secret: envConfigs.razorpayAptSecret,
//         });

//         const options={
//         amount: amount * 100,
//         currency: currency,
//         }
//         return await instance.orders.create(options)  
//     } catch (error) {
//         throw new Error(error)
//     }
//     }

//   static createCashfreeOrder = async (amount: number, currency: string, orderId: string, userId: string, customerPhone: string): Promise<any> => {
//     try {
//       const request = {
//         order_amount: amount,
//         order_currency: currency,
//         order_id: orderId,
//         customer_details: {
//           customer_id: userId,
//           customer_phone: customerPhone,
//         },
//         // order_meta: {
//         //   return_url: `https://www.cashfree.com/devstudio/preview/pg/web/checkout?order_id={order_id}`,
//         // },
//       };
//       const response = await Cashfree.PGCreateOrder("2023-08-01", request);
//       logger.info(response.data);
//       return response.data;
//     } catch (error) {
//       throw new Error(error.response.data.message);
//     }
//   };


// }