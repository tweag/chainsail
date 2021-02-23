import Link from 'next/link';
import firebase from 'firebase/app';

import { FlexRow } from './Flex';
import { useAuth } from './Auth';
import firebaseClient from '../utils/firebaseClient';

const NavItem = (props) => {
  const style =
    'px-4 py-2 mx-2 border-white border-opacity-20 hover:opacity-60 transition duration-300 cursor-pointer';
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
  return (
    <FlexRow className="items-center h-16 text-sm md:text-base">
      <NavItem internal href="/">
        Home
      </NavItem>
      {!user && (
        <NavItem internal href="/login">
          Login
        </NavItem>
      )}
      {user && <NavItem onClick={logout}>Logout</NavItem>}
    </FlexRow>
  );
};
export default Navbar;
