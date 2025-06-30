import {Request,Response} from "express"
import { envConfigs } from "../config/envconfig";
import axios from "axios";
import dbservices from "../services/dbservices";
import url from "node:url";







export class auth{

   static googleSignInSignUp = async (req: Request, res: Response) => {
    try {
      const token = req.query.code;
      console.log("token:", token);
      let clientId = envConfigs.googleClientId;
      let clientSecret = envConfigs.googleClientSecret;
      let REDIRECT_URI = envConfigs.redirectUri;
      console.log("REDIRECT_URI ", REDIRECT_URI);

      const validateUser = await axios.post(
        `https://oauth2.googleapis.com/token`,
        {
          code: token,
          client_id: clientId,
          client_secret: clientSecret,
          redirect_uri: REDIRECT_URI,
          grant_type: "authorization_code",
        }
      );
      console.log("done");
      

      const { id_token, access_token } = validateUser.data;
      const { email, name, picture } = await axios
        .get(
          `https://www.googleapis.com/oauth2/v1/userinfo?alt=json&access_token=${access_token}`,
          {
            headers: {
              Authorization: `Bearer ${id_token}`,
            },
          }
        )
        .then((res) => res.data)
        .catch((error) => {
          throw new Error(error.message);
        });
      if (!email) throw new Error("Error fetching email please try again");
      const genToken = await dbservices.auth.googleLogIn(email, name, picture);
      

      
      const userDetails = {
        id: genToken.user.id,
        name: genToken.user.name,
        picture,
        email: genToken.user.email,
        accessToken: genToken.token,
       
      };
      console.log("acessToken :", genToken.token);

      let FRONTEND_REDIRECT_URL = process.env.FRONTEND_REDIRECT_URL;

      return res.redirect(
        url.format({
          pathname: `${FRONTEND_REDIRECT_URL}`,
          query: { user: JSON.stringify(userDetails) },
        })
      );
    } catch (error) {
      console.log(error);
      //logger.error(`Error in google auth:${error}`);

      let FRONTEND_REDIRECT_URL = process.env.FRONTEND_REDIRECT_URL;

      return res.redirect(
        url.format({
          pathname: `${FRONTEND_REDIRECT_URL}`,
          query: { user: JSON.stringify({}) },
        })
      );
    }
  };
  
      
}