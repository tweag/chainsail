import { withAuthUser, AuthAction } from 'next-firebase-auth';
import { FlexCenter, FirebaseAuth } from '../components';

const Login = () => (
  <FlexCenter className="w-full h-screen bg-purple-900">
    <FirebaseAuth />
  </FlexCenter>
);

export default withAuthUser({
  whenAuthed: AuthAction.REDIRECT_TO_APP,
  whenUnauthedBeforeInit: AuthAction.RETURN_NULL,
  whenUnauthedAfterInit: AuthAction.RENDER,
})(Login);
