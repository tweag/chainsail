import { withAuthUser, AuthAction } from 'next-firebase-auth';
import { FlexCenter, FirebaseAuth, FlexCol } from '../components';

const Login = () => (
  <FlexCenter className="h-screen w-full">
    <FlexCol>
      <h3>Sign in</h3>
      <div>
        <p>
          This auth page is <b>static</b>. It will redirect on the client side if the user is
          already authenticated.
        </p>
      </div>
      <FirebaseAuth />
    </FlexCol>
  </FlexCenter>
);

export default withAuthUser({
  whenAuthed: AuthAction.REDIRECT_TO_APP,
  whenUnauthedBeforeInit: AuthAction.RETURN_NULL,
  whenUnauthedAfterInit: AuthAction.RENDER,
})(Login);
