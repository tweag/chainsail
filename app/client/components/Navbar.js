import Link from 'next/link';
import firebase from 'firebase/app';

import { FlexRow } from './Flex';
import { useAuth } from './Auth';

const NavItem = (props) => {
  const style = `px-6 py-1 border-white border-opacity-20 hover:opacity-60 transition duration-300 cursor-pointer ${props.className}`;
  if (props.internal) {
    return (
      <Link href={props.href}>
        <a className={style}>{props.children}</a>
      </Link>
    );
  }
  if (props.href) {
    return (
      <a className={style} href={props.href}>
        {props.children}
      </a>
    );
  }
  if (props.onClick) {
    return (
      <a className={style} onClick={props.onClick}>
        {props.children}
      </a>
    );
  }
};

const logout = async () => {
  await firebase.auth().signOut();
  window.location.href = '/';
};

const Navbar = () => {
  const { user } = useAuth();
  const styleLogInOut = 'border-white rounded-md border-2';
  return (
    <FlexRow between className="items-center h-16 text-sm md:text-base">
      <NavItem internal href="/">
        Home
      </NavItem>
      <div>
        {!user && (
          <NavItem internal href="/login" className={styleLogInOut}>
            Login
          </NavItem>
        )}
        {user && (
          <NavItem onClick={logout} className={styleLogInOut}>
            Logout
          </NavItem>
        )}
      </div>
    </FlexRow>
  );
};
export default Navbar;
